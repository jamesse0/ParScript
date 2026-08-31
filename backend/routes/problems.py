"""Read-only problem endpoints (DESIGN.md §5).

Owner: Supabase person (DESIGN.md §8.1). Implement against dataaccess/problems.py.

  GET /problems            list, filterable by ?difficulty=
  GET /problems/{id}       full detail incl. starter_code, test_cases
"""

from fastapi import APIRouter

router = APIRouter(tags=["problems"])


@router.get("/problems")
async def list_problems(difficulty: str | None = None):
    raise NotImplementedError


@router.get("/problems/{problem_id}")
async def get_problem(problem_id: str):
    raise NotImplementedError
