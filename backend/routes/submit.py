"""Submission endpoint (DESIGN.md §5, §6).

Owner: Docker person (DESIGN.md §8.2).

  POST /submit  {problem_id, code, input_tokens, output_tokens, elapsed_seconds, attempt_id?}
    1. read problems grading fields (test_kind + test_cases/function_signature
       or the hidden test_file)                        (dataaccess/problems.py)
    2. run code in the Docker sandbox: I/O-pair or pytest per test_kind
                                                       (services/sandbox_runner.py)
    3. insert ONE submissions row, always (pass or fail) (dataaccess/submissions.py)
    -> {passed, test_results, submission_id, attempt_id}

Note: attempts (chat history) is written by routes/chat.py, not here -- see
supabase/migrations/0001_init.sql for the current attempts/submissions split.
"""

from fastapi import APIRouter, Depends, HTTPException

from dataaccess.problems import get_problem_grading
from dataaccess.submissions import insert_submission
from deps import require_profile
from schemas import SubmitRequest, SubmitResponse
from services.sandbox_runner import SandboxError, run_pytest_submission, run_submission

router = APIRouter(tags=["submit"])


@router.post("/submit", response_model=SubmitResponse)
async def submit(body: SubmitRequest, user=Depends(require_profile)) -> SubmitResponse:
    problem = get_problem_grading(body.problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="problem not found")

    # Normalize indentation: the manual editor inserts real tabs, but seeded
    # starter code uses 4 spaces -- mixing the two is a Python 3 TabError.
    # Expand tabs to 4-col stops so what we run (and store) is consistent.
    code = body.code.expandtabs(4)

    try:
        if problem["test_kind"] == "pytest":
            # system_design: run the hidden pytest module against the solution.
            passed, test_results = run_pytest_submission(code, problem["test_file"])
        else:
            passed, test_results = run_submission(
                code, problem["test_cases"], problem["function_signature"]
            )
    except SandboxError as e:
        # Infra-level failure (timeout, crashed container) -- still recorded
        # as a failed run rather than surfaced as a 500, so one bad
        # submission can't break the flow for the user.
        passed, test_results = False, [{"input": None, "expected_output": None, "actual_output": None, "passed": False, "error": str(e)}]

    row = insert_submission(
        user_id=user["id"],
        problem_id=body.problem_id,
        code=code,
        test_results=test_results,
        passed=passed,
        attempt_id=body.attempt_id,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
        elapsed_seconds=body.elapsed_seconds,
        mode=body.mode,
    )

    return SubmitResponse(
        passed=passed,
        test_results=test_results,
        submission_id=row["id"],
        attempt_id=body.attempt_id,
    )
