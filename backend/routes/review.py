"""Review endpoint — one-off OpenAI call (DESIGN.md §5).

Owner: Full-stack generalist (DESIGN.md §8.3). Implement against services/openai_client.py.

  POST /review  {problem_id, code}
    -> {comments}  improvement notes, returned directly (not persisted tonight).
"""

from fastapi import APIRouter

router = APIRouter(tags=["review"])


@router.post("/review")
async def review():
    raise NotImplementedError
