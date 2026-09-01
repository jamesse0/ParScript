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
"""

from fastapi import APIRouter, Query

from dataaccess import submissions as submissions_dao
from schemas import GlobalLeaderboardRow, LeaderboardRow

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
