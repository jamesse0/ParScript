"""problems table reads (DESIGN.md §4): slug, title, description, difficulty,
par_tokens, function_signature, starter_code, test_cases (jsonb), test_kind,
test_file.

Shared by routes/problems.py (full detail) and routes/submit.py (grading fields
only). NOTE: test_file (the hidden pytest module) is fetched ONLY by
get_problem_grading -- it must never reach the client.

Owner: Supabase person (DESIGN.md §8.1).
"""

from dataaccess.supabase_client import get_supabase

_SUMMARY_COLS = "id, slug, title, difficulty, par_tokens"
_DETAIL_COLS = (
    "id, slug, title, description, difficulty, par_tokens, "
    "function_signature, starter_code, test_cases, test_kind"
)
# test_file is deliberately excluded from _DETAIL_COLS (client-facing).
_GRADING_COLS = "id, test_kind, test_cases, test_file, function_signature"


def list_problems(difficulty: str | None = None) -> list[dict]:
    """Problem summaries, oldest first, optionally filtered by difficulty.
    Course-only problems are excluded -- they're reached through their course."""

    def _build(exclude_course_only: bool):
        q = get_supabase().table("problems").select(_SUMMARY_COLS).order("id")
        if exclude_course_only:
            q = q.eq("course_only", False)
        if difficulty:
            q = q.eq("difficulty", difficulty)
        return q

    try:
        return _build(True).execute().data or []
    except Exception as exc:  # noqa: BLE001
        # Tolerate a DB that hasn't run 0005_courses.sql yet. Remove once applied.
        if "course_only" not in str(exc):
            raise
        return _build(False).execute().data or []


def get_problem(problem_id: int | str) -> dict | None:
    """Full detail for one problem, or None if it doesn't exist. Client-facing:
    no test_file."""
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


def get_problem_grading(problem_id: int | str) -> dict | None:
    """Grading fields for one problem (incl. the hidden test_file), or None.
    Used only by routes/submit.py -- never returned to the client."""
    rows = (
        get_supabase()
        .table("problems")
        .select(_GRADING_COLS)
        .eq("id", problem_id)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None
