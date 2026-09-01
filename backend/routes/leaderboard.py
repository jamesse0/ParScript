"""Leaderboard endpoints (DESIGN.md §5, + global leaderboard stretch goal).

Owner: Supabase person (DESIGN.md §8.1). Thin wrapper over dataaccess/submissions.py.

  GET /leaderboard/global?min_solves=3
    Users ranked by handicap (avg tokens-vs-par ratio across solved problems,
    ascending -- lower is better), joined to profiles.username. Must be
    registered before /leaderboard/{problem_id} so "global" isn't swallowed
    by the int path param.

  GET /leaderboard/{problem_id}?mode=prompt|manual   (default: prompt)
    prompt: each user's lowest-token passing run, tokens asc then time asc.
    manual: each user's fastest passing run, time asc.
  Joined to profiles.username.

  GET /submissions/{submission_id}/prompts   (auth)
    The user prompts behind one leaderboard score. Only visible once the
    caller has passed the same problem (or owns the score).
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from dataaccess import attempts as attempts_dao
from dataaccess import submissions as submissions_dao
from deps import require_profile
from schemas import GlobalLeaderboardRow, LeaderboardRow, PromptTraceResponse

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard/global", response_model=list[GlobalLeaderboardRow])
async def get_global_leaderboard(min_solves: int = Query(3, ge=1)):
    return submissions_dao.global_leaderboard(min_solves)


@router.get("/leaderboard/{problem_id}", response_model=list[LeaderboardRow])
async def get_leaderboard(
    problem_id: int,
    mode: str = Query("prompt", pattern="^(prompt|manual)$"),
):
    return submissions_dao.leaderboard_for_problem(problem_id, mode)


@router.get("/submissions/{submission_id}/prompts", response_model=PromptTraceResponse)
async def get_submission_prompts(submission_id: str, user=Depends(require_profile)):
    """The chat prompts behind a leaderboard score. Gated: you must have passed
    the same problem yourself (or own the score) -- no free ride off other
    people's phrasing."""
    submission = submissions_dao.get_submission(submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="submission not found")

    is_owner = submission["user_id"] == user["id"]
    if not is_owner and not submissions_dao.user_has_passed(user["id"], submission["problem_id"]):
        raise HTTPException(
            status_code=403,
            detail="submit a working solution to this problem to view other players' prompts",
        )

    author = submission.get("profiles") or {}
    if isinstance(author, list):
        author = author[0] if author else {}
    username = author.get("username", "")

    attempt_id = submission.get("attempt_id")
    attempt = attempts_dao.get_attempt(attempt_id) if attempt_id else None
    if attempt is None:
        return PromptTraceResponse(username=username, has_trace=False, prompts=[])

    history = attempt.get("message_history") or []
    prompts = [
        m.get("content", "")
        for m in history
        if isinstance(m, dict) and m.get("role") == "user"
    ]
    return PromptTraceResponse(
        username=username,
        has_trace=bool(prompts),
        prompts=prompts,
        model=attempt.get("model"),
        created_at=attempt.get("created_at"),
    )
