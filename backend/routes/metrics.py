"""Personal metrics endpoint (DESIGN.md §5).

Owner: Supabase person (DESIGN.md §8.1). Thin wrapper over dataaccess/submissions.py.

  GET /me/metrics
    totals solved, avg tokens-vs-par ratio (overall + by difficulty),
    history table for the logged-in user, scoped to submissions.
"""

from fastapi import APIRouter, Depends

from dataaccess import submissions as submissions_dao
from deps import get_current_user
from schemas import MetricsResponse

router = APIRouter(tags=["metrics"])


@router.get("/me/metrics", response_model=MetricsResponse)
async def get_my_metrics(user=Depends(get_current_user)):
    return submissions_dao.metrics_for_user(user["id"])
