"""Docker sandbox driver (DESIGN.md §6).

Writes a temp file combining the sandbox/runner.py harness + the submitted code,
then runs:

    docker run --rm --network none --memory 256m --cpus 0.5 <settings.sandbox_image> ...

with a wall-clock timeout (settings.sandbox_timeout_seconds) so a looping LLM
solution can't hang a submission. Parses the harness's single JSON result line
into a per-test pass/fail list + overall passed bool.

Owner: Docker person (DESIGN.md §8.2).
"""

import json
import re
import subprocess
import tempfile
from pathlib import Path

from config import settings

_RUNNER_TEMPLATE = Path(__file__).parent.parent / "sandbox" / "runner.py"
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
    return (
        f"{before}{_INSERTION_MARKER}\n"
        f"{code}\n\n"
        f"__FUNCTION_NAME__ = {function_name!r}\n"
        f"__TEST_CASES__ = {json.dumps(test_cases)}\n"
        f"{after}"
    )


def run_submission(code: str, test_cases: list[dict], function_signature: str):
    """-> (passed: bool, test_results: list[dict])

    Raises SandboxError for infra failures only (timeout / crash / bad
    output) -- callers should treat that as a failed run, not a 500.
    """
    function_name = _extract_function_name(function_signature)
    combined_source = _build_combined_source(code, function_name, test_cases)

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "runner.py").write_text(combined_source)

        try:
            proc = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "--network", "none",
                    "--memory", "256m",
                    "--cpus", "0.5",
                    "-v", f"{tmpdir}:/sandbox:ro",
                    settings.sandbox_image,
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
            result = json.loads(last_line)
        except (json.JSONDecodeError, IndexError):
            raise SandboxError(f"sandbox produced no parseable result. stdout={proc.stdout!r} stderr={proc.stderr!r}")

    return bool(result.get("passed", False)), result.get("results", [])
