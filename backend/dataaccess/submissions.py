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
    """Leaderboard rows for one problem: each user's best (lowest total tokens)
    passing run, ordered by total tokens asc, then elapsed_seconds asc.

    Reads raw `submissions` rows (every attempt is stored, pass or fail) and
    picks the best per user_id here rather than via a DB view, so all
    submissions still live in the table untouched.
    """
    rows = (
        get_supabase()
        .table("submissions")
        .select("user_id, input_tokens, output_tokens, elapsed_seconds, created_at, profiles(username)")
        .eq("problem_id", problem_id)
        .eq("passed", True)
        .execute()
        .data
        or []
    )

    best_by_user: dict[str, dict] = {}
    for row in rows:
        profile = row.get("profiles") or {}
        if isinstance(profile, list):  # tolerate array-shaped embed
            profile = profile[0] if profile else {}
        total_input_tokens = row.get("input_tokens") or 0
        total_output_tokens = row.get("output_tokens") or 0
        total_tokens = total_input_tokens + total_output_tokens

        user_id = row["user_id"]
        existing = best_by_user.get(user_id)
        if existing is not None and existing["total_tokens"] <= total_tokens:
            continue

        best_by_user[user_id] = {
            "username": profile.get("username", ""),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
            "elapsed_seconds": float(row.get("elapsed_seconds") or 0),
            "created_at": row.get("created_at"),
        }

    return sorted(
        best_by_user.values(), key=lambda r: (r["total_tokens"], r["elapsed_seconds"])
    )


def metrics_for_user(user_id: str) -> dict:
    """Aggregates + history for GET /me/metrics, scoped to this user's submissions.

    Returns a dict matching schemas.MetricsResponse:
      total_solved, avg_tokens_vs_par, avg_tokens_vs_par_by_difficulty, history.

    Both the aggregates and the history are keyed off each problem's *best*
    passing submission (lowest total_tokens) -- not every attempt, and not
    just the first one to pass.
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

    # best (lowest total_tokens) passing submission per problem_id
    best_pass: dict[int, dict] = {}

    for row in rows:
        if not row.get("passed"):
            continue

        problem = row.get("problems") or {}
        if isinstance(problem, list):  # tolerate array-shaped embed
            problem = problem[0] if problem else {}
        par_tokens = problem.get("par_tokens") or 0
        total_tokens = (row.get("input_tokens") or 0) + (row.get("output_tokens") or 0)

        problem_id = row["problem_id"]
        existing = best_pass.get(problem_id)
        if existing is not None and existing["total_tokens"] <= total_tokens:
            continue

        best_pass[problem_id] = {
            "problem_title": problem.get("title", ""),
            "total_tokens": total_tokens,
            "par_tokens": par_tokens,
            "elapsed_seconds": float(row.get("elapsed_seconds") or 0),
            "passed": True,
            "created_at": row.get("created_at"),
            "difficulty": problem.get("difficulty", "unknown"),
            "ratio": (total_tokens / par_tokens) if par_tokens else None,
        }

    history = [
        {k: v for k, v in entry.items() if k not in ("difficulty", "ratio")}
        for entry in sorted(
            best_pass.values(), key=lambda e: e["created_at"], reverse=True
        )
    ]

    ratios = [entry["ratio"] for entry in best_pass.values() if entry["ratio"] is not None]
    avg_tokens_vs_par = sum(ratios) / len(ratios) if ratios else 0.0

    by_difficulty: dict[str, list[float]] = defaultdict(list)
    for entry in best_pass.values():
        if entry["ratio"] is not None:
            by_difficulty[entry["difficulty"]].append(entry["ratio"])
    avg_by_difficulty = {
        difficulty: sum(values) / len(values)
        for difficulty, values in by_difficulty.items()
    }

    return {
        "total_solved": len(best_pass),
        "avg_tokens_vs_par": avg_tokens_vs_par,
        "avg_tokens_vs_par_by_difficulty": avg_by_difficulty,
        "history": history,
    }
