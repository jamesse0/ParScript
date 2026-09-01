"""Per-problem leaderboard endpoint (DESIGN.md §5).

Owner: Supabase person (DESIGN.md §8.1). Thin wrapper over dataaccess/submissions.py.

  GET /leaderboard/{problem_id}?mode=prompt|manual   (default: prompt)
    prompt: each user's lowest-token passing run, tokens asc then time asc.
    manual: each user's fastest passing run, time asc.
  Joined to profiles.username.
"""

from fastapi import APIRouter, Query

from dataaccess import submissions as submissions_dao
from schemas import LeaderboardRow

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard/{problem_id}", response_model=list[LeaderboardRow])
async def get_leaderboard(
    problem_id: int,
    mode: str = Query("prompt", pattern="^(prompt|manual)$"),
):
    return submissions_dao.leaderboard_for_problem(problem_id, mode)
