"""Docker sandbox driver (DESIGN.md §6).

Two grading paths, both returning (passed: bool, test_results: list[dict]) and
both parsing the harness's single JSON result line:

  run_submission        test_kind='io_pairs' -- splice submitted code + the
                        sandbox/runner.py harness, compare run_code(*args) == expected.
  run_pytest_submission  test_kind='pytest'  -- run the problem's hidden pytest
                        module against the submitted solution.py via pytest_harness.py.

Both run:

    docker run --rm --network none --memory 256m --cpus 0.5 <settings.sandbox_image> ...

with a wall-clock timeout (settings.sandbox_timeout_seconds) so a looping LLM
solution can't hang a submission.

Owner: Docker person (DESIGN.md §8.2).
"""

import json
import re
import subprocess
import tempfile
from pathlib import Path

from config import settings

_SANDBOX_DIR = Path(__file__).parent.parent / "sandbox"
_RUNNER_TEMPLATE = _SANDBOX_DIR / "runner.py"
_PYTEST_HARNESS = _SANDBOX_DIR / "pytest_harness.py"
_INSERTION_MARKER = "# ---SUBMITTED_CODE_INSERTION_POINT---"


class SandboxError(Exception):
    """Infrastructure-level failure (timeout, container crash, unparseable
    output) -- distinct from the submission simply failing its tests, which
    is a normal (passed=False, test_results=[...]) return."""


def _extract_function_name(function_signature: str) -> str:
    """function_signature is stored as text like 'def twoSum(nums, target):'."""
    match = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", function_signature)
    if not match:
        raise ValueError(f"could not parse a function name from signature: {function_signature!r}")
    return match.group(1)


def _build_combined_source(code: str, function_name: str, test_cases: list[dict]) -> str:
    template = _RUNNER_TEMPLATE.read_text()
    if _INSERTION_MARKER not in template:
        raise SandboxError("runner.py template is missing the insertion marker")

    before, after = template.split(_INSERTION_MARKER, 1)
    # Embed test_cases as a JSON string the harness decodes at runtime, NOT as a
    # raw literal: json.dumps() emits true/false/null, which aren't valid Python
    # (a boolean expected_output would blow up the harness with a NameError).
    return (
        f"{before}{_INSERTION_MARKER}\n"
        f"{code}\n\n"
        f"__FUNCTION_NAME__ = {function_name!r}\n"
        f"__TEST_CASES__ = json.loads({json.dumps(test_cases)!r})\n"
        f"{after}"
    )


def _run_container(tmpdir: str, *cmd: str) -> dict:
    """Run the sandbox image over `tmpdir` (mounted read-only at /sandbox) and
    return the harness's parsed JSON result. `cmd` overrides the image CMD when
    given (the pytest path passes `"python", "pytest_harness.py"`).

    Raises SandboxError for infra failures only (timeout / crash / bad output).
    """
    try:
        proc = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", "256m",
                "--cpus", "0.5",
                "-v", f"{tmpdir}:/sandbox:ro",
                settings.sandbox_image,
                *cmd,
            ],
            capture_output=True,
            text=True,
            timeout=settings.sandbox_timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        raise SandboxError(f"submission timed out after {settings.sandbox_timeout_seconds}s")

    if proc.returncode != 0 and not proc.stdout.strip():
        raise SandboxError(f"sandbox container crashed: {proc.stderr.strip()[:2000]}")

    last_line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    try:
        return json.loads(last_line)
    except (json.JSONDecodeError, IndexError):
        raise SandboxError(f"sandbox produced no parseable result. stdout={proc.stdout!r} stderr={proc.stderr!r}")


def run_submission(code: str, test_cases: list[dict], function_signature: str):
    """I/O-pair grading (test_kind='io_pairs') -> (passed: bool, test_results: list[dict]).

    Raises SandboxError for infra failures only (timeout / crash / bad
    output) -- callers should treat that as a failed run, not a 500.
    """
    function_name = _extract_function_name(function_signature)
    combined_source = _build_combined_source(code, function_name, test_cases)

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "runner.py").write_text(combined_source)
        result = _run_container(tmpdir)

    return bool(result.get("passed", False)), result.get("results", [])


def run_pytest_submission(code: str, test_file: str):
    """pytest grading (test_kind='pytest') -> (passed: bool, test_results: list[dict]).

    Writes the submitted code as solution.py, the problem's hidden pytest module
    as test_solution.py, and the checked-in pytest_harness.py alongside them,
    then runs `python pytest_harness.py` in the sandbox. Same return contract
    and same SandboxError semantics as run_submission.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "solution.py").write_text(code)
        Path(tmpdir, "test_solution.py").write_text(test_file)
        Path(tmpdir, "pytest_harness.py").write_text(_PYTEST_HARNESS.read_text())
        result = _run_container(tmpdir, "python", "pytest_harness.py")

    return bool(result.get("passed", False)), result.get("results", [])
