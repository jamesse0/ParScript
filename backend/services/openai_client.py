"""OpenAI glue for /chat and /review (DESIGN.md §3, §5).

Cheap model (settings.openai_model, e.g. gpt-5-nano). Returns generated text
plus token usage from the API response.

Owner: Full-stack generalist (DESIGN.md §8.3).
"""


def chat_completion(problem, message_history):
    """-> (reply: str, code: str, input_tokens: int, output_tokens: int)"""
    raise NotImplementedError


def review_completion(problem, code):
    """-> comments: str"""
    raise NotImplementedError
