"""OpenAI glue for /chat and /review (DESIGN.md §3, §5).

Cheap reasoning model (settings.openai_model, e.g. gpt-5-nano).

/chat goes through the Responses API so we can ask for a reasoning *summary*
("reasoning": {"summary": "auto"}) -- a short natural-language gist of what the
model had to work out. That's surfaced in the UI so a user can see how a vague
prompt makes the model think harder. The raw chain-of-thought is never exposed
by OpenAI; only the summary and the reasoning-token count are.

Note: `temperature` is intentionally not set. gpt-5 reasoning models reject any
non-default `temperature`/`top_p`, so output already varies call-to-call and
there is no knob to make it less volatile (pass `reasoning.effort` to trade
thinking depth for speed instead). /review keeps that lever at "low".

Owner: Full-stack generalist (DESIGN.md §8.3).
"""

import re

from openai import AsyncOpenAI, OpenAIError

from config import settings

_client: AsyncOpenAI | None = None

# Grab fenced code blocks: ```python / ```py / bare ``` ... ```
_CODE_FENCE = re.compile(r"```[ \t]*(?:python|py)?[ \t]*\r?\n(.*?)```", re.DOTALL | re.IGNORECASE)

# Carries the required function signature (a grading contract -- the sandbox
# harness calls the function by that exact name) but NOT the problem spec. Par
# Prompt tests whether the USER can describe what the function should do.
_CHAT_SYSTEM = """You are a Python coding assistant. The user describes a programming task; you write code that does exactly what they describe.

- Your solution MUST define exactly this function -- same name and parameters -- as the entry point:
      {function_signature}
- Everything else about the task (what it computes, return shape, edge cases, constraints) comes ONLY from the user's messages. Don't infer unstated behavior or assume it's a specific well-known problem unless they say so.
- Reply with ONLY the complete solution inside a single triple-backtick ```python code block. Output nothing else -- no explanation, no prose, no text before or after the code block.
- Standard library only. No test code, no input parsing, no `if __name__ == "__main__"` block.
- When the user asks for a change, return the full updated code again (still just the code block), not a diff."""

_REVIEW_SYSTEM = """You are a senior engineer reviewing a Python solution that already passes its tests.
Respond in EXACTLY this format, with nothing before or after it:

Time: <Big-O time complexity, e.g. O(n log n)>
Space: <Big-O space complexity, e.g. O(1)>

- <first bullet>
- <second bullet>
- <third bullet>

Give 3-5 bullet points total, covering correctness edge cases and readability (not
complexity -- that's already captured above). Each bullet is one short, concrete
sentence. Only suggest a code change if it fits inline using backticks. Be concise."""


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


_TIME_LINE = re.compile(r"^time\s*(?:complexity)?\s*:\s*(.+)$", re.IGNORECASE)
_SPACE_LINE = re.compile(r"^space\s*(?:complexity)?\s*:\s*(.+)$", re.IGNORECASE)
_BULLET_LINE = re.compile(r"^[-*]\s+(.+)$")


def parse_review(text: str) -> tuple[str, str, list[str]]:
    """-> (time_complexity, space_complexity, bullets), tolerating minor drift
    from the requested format (missing fields just come back empty/[])."""
    time_complexity = ""
    space_complexity = ""
    bullets = []
    for line in (text or "").splitlines():
        stripped = line.strip().strip("*").strip()
        if m := _TIME_LINE.match(stripped):
            time_complexity = m.group(1).strip()
        elif m := _SPACE_LINE.match(stripped):
            space_complexity = m.group(1).strip()
        elif m := _BULLET_LINE.match(line.strip()):
            bullets.append(m.group(1).strip())
    return time_complexity, space_complexity, bullets


def _sanitize_history(message_history: list[dict]) -> list[dict]:
    clean = []
    for msg in message_history:
        role = msg.get("role")
        if role not in ("user", "assistant"):
            raise OpenAICallError(f"unexpected message role: {role!r}")
        clean.append({"role": role, "content": msg.get("content", "")})
    return clean


def _extract_reasoning_summary(resp) -> str:
    """Join the reasoning-summary text parts from a Responses API result, if any.
    Empty string when the model returned no summary (some runs won't)."""
    parts = []
    for item in getattr(resp, "output", None) or []:
        if getattr(item, "type", None) != "reasoning":
            continue
        for chunk in getattr(item, "summary", None) or []:
            text = (getattr(chunk, "text", "") or "").strip()
            if text:
                parts.append(text)
    return "\n\n".join(parts)


async def chat_completion(
    function_signature: str, message_history: list[dict]
) -> tuple[str, str, int, int, int, str]:
    """-> (reply, code, input_tokens, output_tokens, reasoning_tokens, reasoning_summary).

    `output_tokens` already includes `reasoning_tokens` (Responses API accounting).
    `reasoning_summary` is a short natural-language gist of the model's thinking
    ("" if the model returned none) -- not the raw chain-of-thought.

    Only `function_signature` crosses the boundary from the problem -- the
    required entry-point name/params, which the grader depends on. The task
    description is NOT passed; the user's messages are the only source of the
    spec (that's what Par Prompt measures).
    """
    system = _CHAT_SYSTEM.format(function_signature=function_signature)

    try:
        resp = await _get_client().responses.create(
            model=settings.openai_model,
            instructions=system,
            input=_sanitize_history(message_history),
            max_output_tokens=settings.openai_max_completion_tokens,
            reasoning={"summary": "auto"},
        )
    except OpenAIError as exc:
        raise OpenAICallError(str(exc)) from exc

    reply = resp.output_text or ""
    if not reply.strip():
        reason = getattr(getattr(resp, "incomplete_details", None), "reason", None)
        raise OpenAICallError(
            f"model returned no text (status={getattr(resp, 'status', '?')}, reason={reason}); "
            "try raising OPENAI_MAX_COMPLETION_TOKENS"
        )

    usage = resp.usage
    reasoning_tokens = getattr(
        getattr(usage, "output_tokens_details", None), "reasoning_tokens", 0
    ) or 0
    return (
        reply,
        extract_code(reply),
        usage.input_tokens,
        usage.output_tokens,
        reasoning_tokens,
        _extract_reasoning_summary(resp),
    )


async def review_completion(problem: dict, code: str) -> tuple[str, str, list[str]]:
    """-> (time_complexity, space_complexity, bullets)."""
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
            # Reviewing already-passing code into a few short bullets doesn't need
            # deep chain-of-thought; the API defaults gpt-5-* to "medium" reasoning
            # effort, which was the dominant source of /review's latency.
            reasoning_effort="low",
        )
    except OpenAIError as exc:
        raise OpenAICallError(str(exc)) from exc

    text = resp.choices[0].message.content or ""
    if not text.strip():
        raise OpenAICallError("model returned no review text")

    time_complexity, space_complexity, bullets = parse_review(text)
    if not bullets:
        raise OpenAICallError("model response did not match the expected review format")
    return time_complexity, space_complexity, bullets
