"""submissions table (test-case runs) — one row per Run-tests click, never updated.

Columns (see supabase/migrations/0001_init.sql + 0002_add_submission_mode.sql):
  user_id, problem_id, attempt_id (nullable FK -> attempts), code, test_results (jsonb),
  passed, input_tokens, output_tokens, elapsed_seconds, mode ('prompt'|'manual'), created_at.

Every run is recorded, pass or fail. The leaderboard and personal metrics are
DERIVED from here. `mode` splits AI-assisted ('prompt') runs from hand-written
('manual') ones: the prompt leaderboard ranks by tokens, the manual leaderboard
ranks by time, and metrics only ever count 'prompt' runs.

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
    mode: str = "prompt",
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
        "mode": mode,
    }
    return get_supabase().table("submissions").insert(row).execute().data[0]


def get_submission(submission_id: str) -> dict | None:
    """One submission row (+ its author's username), or None. Used by the
    prompt-trace endpoint to resolve a leaderboard score back to its attempt."""
    rows = (
        get_supabase()
        .table("submissions")
        .select("id, user_id, problem_id, attempt_id, mode, passed, profiles(username)")
        .eq("id", submission_id)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


def user_has_passed(user_id: str, problem_id: int | str) -> bool:
    """True if this user has any passing submission for the problem (any mode).
    Gates whether they may view other players' prompt traces for it."""
    rows = (
        get_supabase()
        .table("submissions")
        .select("id")
        .eq("user_id", user_id)
        .eq("problem_id", problem_id)
        .eq("passed", True)
        .limit(1)
        .execute()
        .data
    )
    return bool(rows)


def leaderboard_for_problem(problem_id: int | str, mode: str = "prompt") -> list[dict]:
    """Leaderboard rows for one problem, scoped to `mode`.

    prompt: each user's lowest-token passing run, ordered by tokens asc then time asc.
    manual: each user's fastest passing run, ordered by time asc then created_at asc.

    Reads raw `submissions` rows (every attempt is stored, pass or fail) and picks
    the best per user_id here rather than via a DB view, so all submissions stay
    in the table untouched.
    """
    rows = (
        get_supabase()
        .table("submissions")
        .select(
            "id, user_id, input_tokens, output_tokens, elapsed_seconds, created_at, "
            "profiles(username)"
        )
        .eq("problem_id", problem_id)
        .eq("mode", mode)
        .eq("passed", True)
        .execute()
        .data
        or []
    )

    is_manual = mode == "manual"

    best_by_user: dict[str, dict] = {}
    for row in rows:
        profile = row.get("profiles") or {}
        if isinstance(profile, list):  # tolerate array-shaped embed
            profile = profile[0] if profile else {}
        total_input_tokens = row.get("input_tokens") or 0
        total_output_tokens = row.get("output_tokens") or 0
        total_tokens = total_input_tokens + total_output_tokens
        elapsed_seconds = float(row.get("elapsed_seconds") or 0)

        # metric that decides "best" for this mode: lower is better
        rank_key = elapsed_seconds if is_manual else total_tokens

        user_id = row["user_id"]
        existing = best_by_user.get(user_id)
        if existing is not None and existing["_rank_key"] <= rank_key:
            continue

        best_by_user[user_id] = {
            "_rank_key": rank_key,
            "user_id": user_id,
            "submission_id": row.get("id"),
            "username": profile.get("username", ""),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
            "elapsed_seconds": elapsed_seconds,
            "created_at": row.get("created_at"),
        }

    if is_manual:
        ordered = sorted(
            best_by_user.values(),
            key=lambda r: (r["elapsed_seconds"], r["created_at"] or ""),
        )
    else:
        ordered = sorted(
            best_by_user.values(),
            key=lambda r: (r["total_tokens"], r["elapsed_seconds"]),
        )

    for entry in ordered:
        entry.pop("_rank_key", None)
    return ordered


def global_leaderboard(min_solves: int = 3) -> list[dict]:
    """Global leaderboard ranking users by handicap (DESIGN.md stretch goal).

    handicap = average of (best total_tokens / par_tokens) across each distinct
    problem a user has passed at least once -- same ratio metrics_for_user
    computes per-user, aggregated here across all users. Lower is better,
    mirroring golf handicap. Only 'prompt' passing submissions count, and a
    user needs at least `min_solves` distinct solved problems to qualify, so
    one lucky low-token solve can't top the board.
    """
    rows = (
        get_supabase()
        .table("submissions")
        .select(
            "user_id, problem_id, input_tokens, output_tokens, "
            "profiles(username), problems(par_tokens)"
        )
        .eq("mode", "prompt")
        .eq("passed", True)
        .execute()
        .data
        or []
    )

    # best (lowest) total_tokens per user per problem
    best_tokens: dict[tuple[str, int], int] = {}
    par_by_problem: dict[int, int] = {}
    usernames: dict[str, str] = {}

    for row in rows:
        profile = row.get("profiles") or {}
        if isinstance(profile, list):  # tolerate array-shaped embed
            profile = profile[0] if profile else {}
        problem = row.get("problems") or {}
        if isinstance(problem, list):  # tolerate array-shaped embed
            problem = problem[0] if problem else {}
        par_tokens = problem.get("par_tokens") or 0
        if not par_tokens:
            continue  # can't compute a ratio without par

        user_id = row["user_id"]
        problem_id = row["problem_id"]
        total_tokens = (row.get("input_tokens") or 0) + (row.get("output_tokens") or 0)

        usernames[user_id] = profile.get("username", "")
        par_by_problem[problem_id] = par_tokens

        key = (user_id, problem_id)
        if key not in best_tokens or total_tokens < best_tokens[key]:
            best_tokens[key] = total_tokens

    ratios_by_user: dict[str, list[float]] = defaultdict(list)
    for (user_id, problem_id), total_tokens in best_tokens.items():
        ratios_by_user[user_id].append(total_tokens / par_by_problem[problem_id])

    entries = [
        {
            "username": usernames[user_id],
            "handicap": sum(ratios) / len(ratios),
            "problems_solved": len(ratios),
        }
        for user_id, ratios in ratios_by_user.items()
        if len(ratios) >= min_solves
    ]

    return sorted(entries, key=lambda e: e["handicap"])


def metrics_for_user(user_id: str) -> dict:
    """Aggregates + history for GET /me/metrics, scoped to this user's submissions.

    Returns a dict matching schemas.MetricsResponse:
      total_solved, avg_tokens_vs_par, avg_tokens_vs_par_by_difficulty, history.

    Only 'prompt' (AI-assisted) submissions count -- manual runs never appear
    here. Both the aggregates and the history are keyed off each problem's *best*
    passing submission (lowest total_tokens), not every attempt.
    """
    rows = (
        get_supabase()
        .table("submissions")
        .select(
            "problem_id, passed, input_tokens, output_tokens, elapsed_seconds, "
            "created_at, problems(title, par_tokens, difficulty)"
        )
        .eq("user_id", user_id)
        .eq("mode", "prompt")
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
