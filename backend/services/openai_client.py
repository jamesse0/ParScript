"""OpenAI glue for /chat and /review (DESIGN.md §3, §5).

Cheap reasoning model (settings.openai_model, e.g. gpt-5-nano). Each call returns
the generated text plus token usage straight from the API response; the frontend
accumulates tokens client-side for the live counter (DESIGN §5, §9).

Owner: Full-stack generalist (DESIGN.md §8.3).
"""

import re

from openai import AsyncOpenAI, OpenAIError

from config import settings

_client: AsyncOpenAI | None = None

# Grab fenced code blocks: ```python / ```py / bare ``` ... ```
_CODE_FENCE = re.compile(r"```[ \t]*(?:python|py)?[ \t]*\r?\n(.*?)```", re.DOTALL | re.IGNORECASE)

# Deliberately problem-agnostic. Par Prompt tests whether the USER can describe
# the problem well enough to get a correct solution -- so the system prompt only
# fixes the output format and never carries the problem spec.
_CHAT_SYSTEM = """You are a Python coding assistant. The user describes a programming task; you write code that does exactly what they describe.

- Give a brief explanation, then the COMPLETE solution as a single ```python code block.
- Standard library only. No test code, no input parsing, no `if __name__ == "__main__"` block.
- Work only from what the user tells you. Don't assume unstated requirements or that it's a specific well-known problem unless they say so.
- When the user asks for a change, return the full updated code again, not a diff."""

_REVIEW_SYSTEM = """You are a senior engineer reviewing a Python solution that already passes its tests.
Give 3-5 short, concrete bullet points: correctness edge cases, time/space complexity,
and readability. Only suggest a code change if it fits on one line. Be concise."""


class OpenAICallError(Exception):
    """The OpenAI request failed, or returned nothing usable."""


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise OpenAICallError("OPENAI_API_KEY is not set")
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


def extract_code(text: str) -> str:
    """Return the last fenced code block in `text`, or '' if there is none
    (the frontend then keeps whatever code was already in the editor)."""
    blocks = _CODE_FENCE.findall(text or "")
    return blocks[-1].strip() if blocks else ""


def _sanitize_history(message_history: list[dict]) -> list[dict]:
    clean = []
    for msg in message_history:
        role = msg.get("role")
        if role not in ("user", "assistant"):
            raise OpenAICallError(f"unexpected message role: {role!r}")
        clean.append({"role": role, "content": msg.get("content", "")})
    return clean


async def chat_completion(message_history: list[dict]) -> tuple[str, str, int, int]:
    """-> (reply, code, input_tokens, output_tokens) for this one call.

    The problem is NOT passed in on purpose -- the user's messages are the only
    source of the spec (that's what Par Prompt measures).
    """
    messages = [{"role": "system", "content": _CHAT_SYSTEM}, *_sanitize_history(message_history)]

    try:
        resp = await _get_client().chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_completion_tokens=settings.openai_max_completion_tokens,
        )
    except OpenAIError as exc:
        raise OpenAICallError(str(exc)) from exc

    choice = resp.choices[0]
    reply = choice.message.content or ""
    if not reply.strip():
        raise OpenAICallError(
            f"model returned no text (finish_reason={choice.finish_reason}); "
            "try raising OPENAI_MAX_COMPLETION_TOKENS"
        )

    usage = resp.usage
    return reply, extract_code(reply), usage.prompt_tokens, usage.completion_tokens


async def review_completion(problem: dict, code: str) -> str:
    """-> improvement comments (plain text / markdown bullets)."""
    user = (
        f"Problem: {problem['title']}\n{problem['description']}\n\n"
        f"Solution:\n```python\n{code}\n```"
    )
    try:
        resp = await _get_client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _REVIEW_SYSTEM},
                {"role": "user", "content": user},
            ],
            max_completion_tokens=settings.openai_max_completion_tokens,
        )
    except OpenAIError as exc:
        raise OpenAICallError(str(exc)) from exc

    comments = resp.choices[0].message.content or ""
    if not comments.strip():
        raise OpenAICallError("model returned no review text")
    return comments
