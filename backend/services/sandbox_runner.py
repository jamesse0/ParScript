"""Docker sandbox driver (DESIGN.md §6).

Writes a temp file combining the sandbox/runner.py harness + the submitted code,
then runs:

    docker run --rm --network none --memory 256m --cpus 0.5 <settings.sandbox_image> ...

with a wall-clock timeout (settings.sandbox_timeout_seconds) so a looping LLM
solution can't hang a submission. Parses the harness's single JSON result line
into a per-test pass/fail list + overall passed bool.

Owner: Docker person (DESIGN.md §8.2).
"""


def run_submission(code: str, test_cases: list[dict], function_signature: str):
    """-> (passed: bool, test_results: list[dict])"""
    raise NotImplementedError
