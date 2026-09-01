"""Review endpoint — one-off OpenAI call (DESIGN.md §5).

Owner: Full-stack generalist (DESIGN.md §8.3). Implemented against services/openai_client.py.

  POST /review  {problem_id, code}
    -> {time_complexity, space_complexity, comments}  returned directly (not persisted tonight).
"""

from fastapi import APIRouter, Depends, HTTPException

from dataaccess.problems import get_problem
from deps import get_current_user
from schemas import ReviewRequest, ReviewResponse
from services.openai_client import OpenAICallError, review_completion

router = APIRouter(tags=["review"])


@router.post("/review", response_model=ReviewResponse)
async def review(body: ReviewRequest, user=Depends(get_current_user)) -> ReviewResponse:
    problem = get_problem(body.problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="problem not found")

    try:
        time_complexity, space_complexity, comments = await review_completion(problem, body.code)
    except OpenAICallError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI call failed: {exc}")

    return ReviewResponse(
        time_complexity=time_complexity, space_complexity=space_complexity, comments=comments
    )
