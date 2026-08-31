"""Read-only problem endpoints (DESIGN.md §5).

Owner: Supabase person (DESIGN.md §8.1). Thin wrappers over dataaccess/problems.py.

  GET /problems            list, filterable by ?difficulty=
  GET /problems/{id}       full detail incl. starter_code, test_cases
"""

from fastapi import APIRouter, HTTPException, Query

from dataaccess import problems as problems_dao
from schemas import ProblemDetail, ProblemSummary

router = APIRouter(tags=["problems"])


@router.get("/problems", response_model=list[ProblemSummary])
async def list_problems(
    difficulty: str | None = Query(default=None, pattern="^(easy|medium|hard)$"),
):
    return problems_dao.list_problems(difficulty)


@router.get("/problems/{problem_id}", response_model=ProblemDetail)
async def get_problem(problem_id: int):
    problem = problems_dao.get_problem(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem
