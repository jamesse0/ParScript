"""Per-problem leaderboard endpoint (DESIGN.md §5).

Owner: Supabase person (DESIGN.md §8.1). Thin wrapper over dataaccess/submissions.py.

  GET /leaderboard/{problem_id}
    earliest passing run per user for that problem, ordered by total tokens asc,
    tiebreak elapsed_seconds asc, joined to profiles.username.
"""

from fastapi import APIRouter

from dataaccess import submissions as submissions_dao
from schemas import LeaderboardRow

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard/{problem_id}", response_model=list[LeaderboardRow])
async def get_leaderboard(problem_id: int):
    return submissions_dao.leaderboard_for_problem(problem_id)
