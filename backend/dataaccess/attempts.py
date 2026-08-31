"""attempts table (chat submissions) — one row per Chat-submit click, never updated.

Columns (see supabase/migrations/0001_init.sql):
  user_id, problem_id, message_history (jsonb: full [{role, content}, ...] sent to
  the model incl. this turn), reply, code, input_tokens, output_tokens, model, created_at.

This is the reproducibility record for how the AI produced code: every prompt and
every response. Test results live on `submissions`, not here.

Schema owned by Supabase person; written by routes/chat.py (full-stack, §8.3).
"""

from dataaccess.supabase_client import get_supabase


def insert_attempt(
    *,
    user_id: str,
    problem_id: int | str,
    message_history: list[dict],
    reply: str | None = None,
    code: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    model: str | None = None,
) -> dict:
    """Insert one attempts row and return it (including the generated id)."""
    row = {
        "user_id": user_id,
        "problem_id": problem_id,
        "message_history": message_history,
        "reply": reply,
        "code": code,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "model": model,
    }
    return get_supabase().table("attempts").insert(row).execute().data[0]
