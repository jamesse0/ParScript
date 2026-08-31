"""Submission endpoint (DESIGN.md §5, §6).

Owner: Docker person (DESIGN.md §8.2).

  POST /submit  {problem_id, code, input_tokens, output_tokens, elapsed_seconds, attempt_id?}
    1. read problems.test_cases / function_signature   (dataaccess/problems.py)
    2. run code in the Docker sandbox                  (services/sandbox_runner.py)
    3. insert ONE submissions row, always (pass or fail) (dataaccess/submissions.py)
    -> {passed, test_results, submission_id, attempt_id}

Note: attempts (chat history) is written by routes/chat.py, not here -- see
supabase/migrations/0001_init.sql for the current attempts/submissions split.
"""

from fastapi import APIRouter, Depends, HTTPException

from dataaccess.problems import get_problem
from dataaccess.submissions import insert_submission
from deps import require_profile
from schemas import SubmitRequest, SubmitResponse
from services.sandbox_runner import SandboxError, run_submission

router = APIRouter(tags=["submit"])


@router.post("/submit", response_model=SubmitResponse)
async def submit(body: SubmitRequest, user=Depends(require_profile)) -> SubmitResponse:
    problem = get_problem(body.problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="problem not found")

    try:
        passed, test_results = run_submission(
            body.code, problem["test_cases"], problem["function_signature"]
        )
    except SandboxError as e:
        # Infra-level failure (timeout, crashed container) -- still recorded
        # as a failed run rather than surfaced as a 500, so one bad
        # submission can't break the flow for the user.
        passed, test_results = False, [{"input": None, "expected_output": None, "actual_output": None, "passed": False, "error": str(e)}]

    row = insert_submission(
        user_id=user["id"],
        problem_id=body.problem_id,
        code=body.code,
        test_results=test_results,
        passed=passed,
        attempt_id=body.attempt_id,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
        elapsed_seconds=body.elapsed_seconds,
    )

    return SubmitResponse(
        passed=passed,
        test_results=test_results,
        submission_id=row["id"],
        attempt_id=body.attempt_id,
    )
