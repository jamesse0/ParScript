"""Per-problem leaderboard endpoint (DESIGN.md §5).

Owner: Supabase person (DESIGN.md §8.1). Implement against dataaccess/submissions.py.

  GET /leaderboard/{problem_id}
    submissions for that problem, ordered by total tokens asc,
    tiebreak elapsed_seconds asc, joined to profiles.username.
"""

from fastapi import APIRouter

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard/{problem_id}")
async def get_leaderboard(problem_id: str):
    raise NotImplementedError
