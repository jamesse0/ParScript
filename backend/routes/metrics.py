"""Personal metrics endpoint (DESIGN.md §5).

Owner: Supabase person (DESIGN.md §8.1). Implement against dataaccess/submissions.py.

  GET /me/metrics
    totals solved, avg tokens-vs-par ratio (overall + by difficulty),
    history table for the logged-in user, scoped to submissions.
"""

from fastapi import APIRouter, Depends

from deps import get_current_user

router = APIRouter(tags=["metrics"])


@router.get("/me/metrics")
async def get_my_metrics(user=Depends(get_current_user)):
    raise NotImplementedError
