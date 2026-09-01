"""attempts table (chat submissions) — one row per Chat-submit click, never updated.

Columns (see supabase/migrations/0001_init.sql + 0004_add_attempt_reasoning.sql):
  user_id, problem_id, message_history (jsonb: full [{role, content}, ...] sent to
  the model incl. this turn), reply, code, input_tokens, output_tokens,
  reasoning_tokens, reasoning_summary, model, created_at.

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
    reasoning_tokens: int = 0,
    reasoning_summary: str | None = None,
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
        "reasoning_tokens": reasoning_tokens,
        "reasoning_summary": reasoning_summary,
        "model": model,
    }
    table = get_supabase().table("attempts")
    try:
        return table.insert(row).execute().data[0]
    except Exception as exc:  # noqa: BLE001
        # Tolerate a DB that hasn't run 0004_add_attempt_reasoning.sql yet:
        # persist the rest of the record so /chat keeps working. Remove this
        # fallback once the migration is applied everywhere.
        if "reasoning_" not in str(exc):
            raise
        row.pop("reasoning_tokens", None)
        row.pop("reasoning_summary", None)
        return table.insert(row).execute().data[0]


def get_attempt(attempt_id: str) -> dict | None:
    """One attempt row, or None. `message_history` holds the full
    [{role, content}, ...] conversation up to and including that turn -- the
    prompt-trace endpoint filters it to the user's messages."""
    rows = (
        get_supabase()
        .table("attempts")
        .select("id, user_id, problem_id, message_history, model, created_at")
        .eq("id", attempt_id)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None
