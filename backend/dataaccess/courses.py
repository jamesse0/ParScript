"""courses / course_problems / course_completions reads + the completion write.

A course is an ordered list of course-only problems (problems.course_only = true,
hidden from the normal list). The course score is total tokens across the
sequence, computed from the real `submissions` rows the client reports back --
verified server-side, not a client-trusted sum.

Aggregation is done in Python over PostgREST embeds, matching
dataaccess/submissions.py (leaderboard_for_problem / metrics_for_user).

Owner: Supabase person (DESIGN.md §8.1).
"""

from fastapi import HTTPException

from dataaccess.supabase_client import get_supabase


def _embed_one(value):
    """PostgREST embeds come back as a dict or a 1-element list; normalize."""
    if isinstance(value, list):
        return value[0] if value else {}
    return value or {}


def _course_row(slug: str) -> dict | None:
    rows = (
        get_supabase()
        .table("courses")
        .select(
            "id, slug, title, description, "
            "course_problems(position, problems(id, title, par_tokens))"
        )
        .eq("slug", slug)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


def _steps(course_row: dict) -> list[dict]:
    steps = []
    for cp in course_row.get("course_problems") or []:
        problem = _embed_one(cp.get("problems"))
        if not problem:
            continue
        steps.append(
            {
                "position": cp["position"],
                "problem_id": problem["id"],
                "title": problem.get("title", ""),
                "par_tokens": problem.get("par_tokens", 0) or 0,
            }
        )
    steps.sort(key=lambda s: s["position"])
    return steps


def list_courses() -> list[dict]:
    """Course summaries (slug, title, description, step_count, summed par)."""
    rows = (
        get_supabase()
        .table("courses")
        .select("slug, title, description, course_problems(position, problems(par_tokens))")
        .order("id")
        .execute()
        .data
        or []
    )
    out = []
    for row in rows:
        cps = row.get("course_problems") or []
        par = sum((_embed_one(cp.get("problems")).get("par_tokens") or 0) for cp in cps)
        out.append(
            {
                "slug": row["slug"],
                "title": row["title"],
                "description": row["description"],
                "step_count": len(cps),
                "par_tokens": par,
            }
        )
    return out


def get_course(slug: str) -> dict | None:
    """Full detail for one course: metadata + ordered steps. None if unknown."""
    row = _course_row(slug)
    if row is None:
        return None
    steps = _steps(row)
    return {
        "slug": row["slug"],
        "title": row["title"],
        "description": row["description"],
        "step_count": len(steps),
        "par_tokens": sum(s["par_tokens"] for s in steps),
        "steps": steps,
    }


def record_completion(user_id: str, slug: str, submission_ids: list[str]) -> dict:
    """Verify the submitted step results and upsert the user's course score.

    Each id must be one of this user's passing submissions for a problem in the
    course. The stored row keeps whichever run has the lower total tokens.
    Raises HTTPException(404/400) on a bad request.
    """
    sb = get_supabase()
    course = _course_row(slug)
    if course is None:
        raise HTTPException(status_code=404, detail="course not found")
    steps = _steps(course)
    course_problem_ids = {s["problem_id"] for s in steps}
    par_tokens = sum(s["par_tokens"] for s in steps)

    if not submission_ids:
        raise HTTPException(status_code=400, detail="submission_ids is empty")

    rows = (
        sb.table("submissions")
        .select("id, user_id, problem_id, passed, input_tokens, output_tokens, elapsed_seconds")
        .in_("id", submission_ids)
        .execute()
        .data
        or []
    )
    by_id = {r["id"]: r for r in rows}
    total_in = total_out = 0
    total_secs = 0.0
    seen_problems = set()
    for sid in submission_ids:
        r = by_id.get(sid)
        if r is None:
            raise HTTPException(status_code=400, detail=f"unknown submission {sid}")
        if r["user_id"] != user_id:
            raise HTTPException(status_code=400, detail="submission does not belong to you")
        if not r["passed"]:
            raise HTTPException(status_code=400, detail="every step submission must be passing")
        if r["problem_id"] not in course_problem_ids:
            raise HTTPException(status_code=400, detail="submission is not part of this course")
        seen_problems.add(r["problem_id"])
        total_in += r["input_tokens"] or 0
        total_out += r["output_tokens"] or 0
        total_secs += float(r["elapsed_seconds"] or 0)

    if seen_problems != course_problem_ids:
        raise HTTPException(status_code=400, detail="every course step must have a passing submission")

    existing = (
        sb.table("course_completions")
        .select("total_input_tokens, total_output_tokens, elapsed_seconds, completed_at")
        .eq("user_id", user_id)
        .eq("course_id", course["id"])
        .limit(1)
        .execute()
        .data
    )
    new_total = total_in + total_out
    if existing:
        prev = existing[0]
        if (prev["total_input_tokens"] + prev["total_output_tokens"]) <= new_total:
            # keep the better (existing) run
            return {**prev, "par_tokens": par_tokens}

    sb.table("course_completions").upsert(
        {
            "user_id": user_id,
            "course_id": course["id"],
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "elapsed_seconds": round(total_secs, 1),
        },
        on_conflict="user_id,course_id",
    ).execute()

    return {
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "elapsed_seconds": round(total_secs, 1),
        "par_tokens": par_tokens,
        "completed_at": _now_iso(),
    }


def course_leaderboard(slug: str) -> list[dict]:
    """Every user's completion of this course, best (fewest total tokens) first."""
    course = _course_row(slug)
    if course is None:
        raise HTTPException(status_code=404, detail="course not found")

    rows = (
        get_supabase()
        .table("course_completions")
        .select(
            "user_id, total_input_tokens, total_output_tokens, elapsed_seconds, "
            "completed_at, profiles(username)"
        )
        .eq("course_id", course["id"])
        .execute()
        .data
        or []
    )
    out = []
    for r in rows:
        profile = _embed_one(r.get("profiles"))
        out.append(
            {
                "user_id": r["user_id"],
                "username": profile.get("username", ""),
                "total_input_tokens": r["total_input_tokens"] or 0,
                "total_output_tokens": r["total_output_tokens"] or 0,
                "elapsed_seconds": float(r["elapsed_seconds"] or 0),
                "completed_at": r["completed_at"],
            }
        )
    out.sort(
        key=lambda e: (e["total_input_tokens"] + e["total_output_tokens"], e["elapsed_seconds"])
    )
    return out


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
