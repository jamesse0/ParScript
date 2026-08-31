"""submissions table (test-case runs) — one row per Run-tests click, never updated.

Columns (see supabase/migrations/0001_init.sql):
  user_id, problem_id, attempt_id (nullable FK -> attempts), code, test_results (jsonb),
  passed, input_tokens, output_tokens, elapsed_seconds, created_at.

Every run is recorded, pass or fail. The leaderboard and personal metrics are
DERIVED from here: the "first pass" is the earliest passed submission per
(user, problem) -- there is no separate first-pass table.

Schema owned by Supabase person (DESIGN.md §8.1); insert path called by
routes/submit.py (Docker person, §8.2). Read paths back the read-only endpoints.
"""

from collections import defaultdict

from dataaccess.supabase_client import get_supabase


def insert_submission(
    *,
    user_id: str,
    problem_id: int | str,
    code: str,
    test_results: list[dict],
    passed: bool,
    attempt_id: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    elapsed_seconds: float = 0,
) -> dict:
    """Insert one submissions row and return it (including the generated id)."""
    row = {
        "user_id": user_id,
        "problem_id": problem_id,
        "attempt_id": attempt_id,
        "code": code,
        "test_results": test_results,
        "passed": passed,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "elapsed_seconds": elapsed_seconds,
    }
    return get_supabase().table("submissions").insert(row).execute().data[0]


def leaderboard_for_problem(problem_id: int | str) -> list[dict]:
    """Leaderboard rows for one problem: the earliest passing run per user,
    ordered by total tokens asc, then elapsed_seconds asc.

    Reads the `leaderboard_entries` view (earliest passing run per user+problem).
    """
    return (
        get_supabase()
        .table("leaderboard_entries")
        .select(
            "username, total_input_tokens, total_output_tokens, total_tokens, "
            "elapsed_seconds, created_at"
        )
        .eq("problem_id", problem_id)
        .order("total_tokens")
        .order("elapsed_seconds")
        .execute()
        .data
        or []
    )


def metrics_for_user(user_id: str) -> dict:
    """Aggregates + history for GET /me/metrics, scoped to this user's submissions.

    Returns a dict matching schemas.MetricsResponse:
      total_solved, avg_tokens_vs_par, avg_tokens_vs_par_by_difficulty, history.
    """
    rows = (
        get_supabase()
        .table("submissions")
        .select(
            "problem_id, passed, input_tokens, output_tokens, elapsed_seconds, "
            "created_at, problems(title, par_tokens, difficulty)"
        )
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )

    history: list[dict] = []
    # earliest passing submission per problem_id -> (ratio, difficulty)
    first_pass: dict[int, dict] = {}

    for row in rows:
        problem = row.get("problems") or {}
        if isinstance(problem, list):  # tolerate array-shaped embed
            problem = problem[0] if problem else {}
        par_tokens = problem.get("par_tokens") or 0
        total_tokens = (row.get("input_tokens") or 0) + (row.get("output_tokens") or 0)

        history.append(
            {
                "problem_title": problem.get("title", ""),
                "total_tokens": total_tokens,
                "par_tokens": par_tokens,
                "elapsed_seconds": float(row.get("elapsed_seconds") or 0),
                "passed": bool(row.get("passed")),
                "created_at": row.get("created_at"),
            }
        )

        if row.get("passed"):
            # rows are newest-first, so the last write per problem wins = earliest
            first_pass[row["problem_id"]] = {
                "ratio": (total_tokens / par_tokens) if par_tokens else None,
                "difficulty": problem.get("difficulty", "unknown"),
            }

    ratios = [fp["ratio"] for fp in first_pass.values() if fp["ratio"] is not None]
    avg_tokens_vs_par = sum(ratios) / len(ratios) if ratios else 0.0

    by_difficulty: dict[str, list[float]] = defaultdict(list)
    for fp in first_pass.values():
        if fp["ratio"] is not None:
            by_difficulty[fp["difficulty"]].append(fp["ratio"])
    avg_by_difficulty = {
        difficulty: sum(values) / len(values)
        for difficulty, values in by_difficulty.items()
    }

    return {
        "total_solved": len(first_pass),
        "avg_tokens_vs_par": avg_tokens_vs_par,
        "avg_tokens_vs_par_by_difficulty": avg_by_difficulty,
        "history": history,
    }
