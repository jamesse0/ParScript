"""Submission endpoint (DESIGN.md §5, §6).

Owner: Docker person (DESIGN.md §8.2).

  POST /submit  {problem_id, code, input_tokens, output_tokens, elapsed_seconds}
    1. read problems.test_cases / function_signature  (dataaccess/problems.py)
    2. run code in the Docker sandbox               (services/sandbox_runner.py)
    3. insert ONE attempts row, always              (dataaccess/attempts.py)
    4. if passed and no submissions row exists yet for this user+problem,
       insert one                                   (dataaccess/submissions.py)
    -> {passed, test_results, attempt_id}
"""

from fastapi import APIRouter, Depends

from deps import get_current_user

router = APIRouter(tags=["submit"])


@router.post("/submit")
async def submit(user=Depends(get_current_user)):
    raise NotImplementedError
