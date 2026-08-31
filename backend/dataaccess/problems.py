"""problems table reads (DESIGN.md §4): slug, title, description, difficulty,
par_tokens, function_signature, starter_code, test_cases (jsonb).

Shared by routes/problems.py (full detail) and routes/submit.py
(test_cases / function_signature only).

Owner: Supabase person (DESIGN.md §8.1).
"""

from dataaccess.supabase_client import get_supabase

_SUMMARY_COLS = "id, slug, title, difficulty, par_tokens"
_DETAIL_COLS = (
    "id, slug, title, description, difficulty, par_tokens, "
    "function_signature, starter_code, test_cases"
)


def list_problems(difficulty: str | None = None) -> list[dict]:
    """Problem summaries, oldest first, optionally filtered by difficulty."""
    query = get_supabase().table("problems").select(_SUMMARY_COLS).order("id")
    if difficulty:
        query = query.eq("difficulty", difficulty)
    return query.execute().data or []


def get_problem(problem_id: int | str) -> dict | None:
    """Full detail for one problem, or None if it doesn't exist."""
    rows = (
        get_supabase()
        .table("problems")
        .select(_DETAIL_COLS)
        .eq("id", problem_id)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None
