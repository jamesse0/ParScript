"""Tests for the Docker sandbox layer (sandbox/runner.py + services/sandbox_runner.py).

Most of this runs WITHOUT Docker: it splices the harness the same way
services.sandbox_runner does, then executes the combined script with the local
Python interpreter instead of `docker run`. That covers the harness contract
(the single JSON result line, the input-shape handling, error cases).

The real end-to-end path through `docker run` is one opt-in test, skipped unless:
    PARSCRIPT_DOCKER_TESTS=1   and the `parscript-sandbox` image is built.

Run from backend/:
    .venv/bin/python -m unittest discover -s tests
    PARSCRIPT_DOCKER_TESTS=1 .venv/bin/python -m unittest discover -s tests
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.sandbox_runner import (  # noqa: E402
    SandboxError,
    _build_combined_source,
    _extract_function_name,
    run_submission,
)

PROBLEMS = {
    p["slug"]: p
    for p in json.loads((BACKEND_DIR / "db" / "problems.json").read_text())
}

TWO_SUM_OK = """
def run_code(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
"""

TWO_SUM_WRONG = """
def run_code(nums, target):
    return [0, 0]
"""

TWO_SUM_RAISES = """
def run_code(nums, target):
    raise ValueError("boom")
"""

WRONG_NAME = """
def add(nums, target):
    return [0, 1]
"""


def run_harness_locally(code: str, function_signature: str, test_cases: list[dict]) -> dict:
    """What run_submission does, but with `python` instead of `docker run`."""
    fn = _extract_function_name(function_signature)
    combined = _build_combined_source(code, fn, test_cases)
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp, "runner.py")
        script.write_text(combined)
        proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=15,
        )
    last_line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    return json.loads(last_line)


class TestExtractFunctionName(unittest.TestCase):
    def test_plain_signature(self):
        self.assertEqual(_extract_function_name("def two_sum(nums, target):"), "two_sum")

    def test_typed_signature(self):
        sig = "def is_valid(s: str) -> bool:"
        self.assertEqual(_extract_function_name(sig), "is_valid")

    def test_camel_case_and_underscores(self):
        self.assertEqual(_extract_function_name("def reverseList(head):"), "reverseList")
        self.assertEqual(_extract_function_name("def _helper_1(x):"), "_helper_1")

    def test_no_function_raises(self):
        with self.assertRaises(ValueError):
            _extract_function_name("nums, target")


class TestBuildCombinedSource(unittest.TestCase):
    def test_splices_code_and_injects_literals(self):
        cases = [
            {"input": {"nums": [1, 2], "target": 3}, "expected_output": [0, 1]},
            {"input": {"s": "()"}, "expected_output": True},  # bool must survive
        ]
        out = _build_combined_source(TWO_SUM_OK, "run_code", cases)

        self.assertIn("def run_code(nums, target):", out)
        self.assertIn("__FUNCTION_NAME__ = 'run_code'", out)
        # embedded as a JSON string decoded at runtime, not a raw literal
        self.assertIn("__TEST_CASES__ = json.loads(", out)
        self.assertNotIn("expected_output': true", out)
        self.assertNotIn('"expected_output": true, "input"', out)

        # the injected line must eval back to the original cases (True, not "true")
        line = next(ln for ln in out.splitlines() if ln.startswith("__TEST_CASES__ ="))
        self.assertEqual(eval(line.split("=", 1)[1], {"json": json}), cases)

        # submitted code must land after the marker, not before
        marker = "# ---SUBMITTED_CODE_INSERTION_POINT---"
        self.assertLess(out.index(marker), out.index("seen = {}"))


class TestHarnessLocally(unittest.TestCase):
    def test_correct_solution_passes_all_cases(self):
        prob = PROBLEMS["two-sum"]
        result = run_harness_locally(TWO_SUM_OK, prob["function_signature"], prob["test_cases"])

        self.assertTrue(result["passed"])
        self.assertEqual(len(result["results"]), len(prob["test_cases"]))
        for entry in result["results"]:
            self.assertTrue(entry["passed"])
            self.assertEqual(set(entry) >= {"input", "expected_output", "actual_output", "passed"}, True)

    def test_wrong_solution_fails_without_error(self):
        prob = PROBLEMS["two-sum"]
        result = run_harness_locally(TWO_SUM_WRONG, prob["function_signature"], prob["test_cases"])

        self.assertFalse(result["passed"])
        self.assertFalse(result["results"][0]["passed"])
        self.assertNotIn("error", result["results"][0])
        self.assertEqual(result["results"][0]["actual_output"], [0, 0])

    def test_exception_in_solution_is_caught_per_case(self):
        prob = PROBLEMS["two-sum"]
        result = run_harness_locally(TWO_SUM_RAISES, prob["function_signature"], prob["test_cases"])

        self.assertFalse(result["passed"])
        self.assertIn("ValueError: boom", result["results"][0]["error"])
        self.assertIsNone(result["results"][0]["actual_output"])

    def test_missing_target_function_reports_error(self):
        prob = PROBLEMS["two-sum"]
        result = run_harness_locally(WRONG_NAME, prob["function_signature"], prob["test_cases"])

        self.assertFalse(result["passed"])
        self.assertEqual(result["results"], [])
        self.assertIn("run_code", result["error"])

    def test_dict_input_is_passed_as_kwargs(self):
        # valid-parentheses stores input as {"s": "..."} -> harness calls run_code(s=...)
        prob = PROBLEMS["valid-parentheses"]
        code = "def run_code(s):\n    return s.count('(') == s.count(')')\n"
        result = run_harness_locally(code, prob["function_signature"], prob["test_cases"])
        self.assertEqual(len(result["results"]), len(prob["test_cases"]))

    def test_list_input_is_passed_positionally(self):
        code = "def f(a, b):\n    return a + b\n"
        cases = [{"input": [2, 3], "expected_output": 5}, {"input": [1, 1], "expected_output": 2}]
        result = run_harness_locally(code, "def f(a, b):", cases)
        self.assertTrue(result["passed"])


@unittest.skipUnless(
    os.environ.get("PARSCRIPT_DOCKER_TESTS") == "1" and shutil.which("docker"),
    "set PARSCRIPT_DOCKER_TESTS=1 (and build parscript-sandbox) to run the real docker path",
)
class TestDockerSandbox(unittest.TestCase):
    def test_correct_solution_through_docker(self):
        prob = PROBLEMS["two-sum"]
        passed, results = run_submission(
            TWO_SUM_OK, prob["test_cases"], prob["function_signature"]
        )
        self.assertTrue(passed)
        self.assertTrue(all(r["passed"] for r in results))

    def test_infinite_loop_hits_timeout(self):
        from config import settings

        original = settings.sandbox_timeout_seconds
        settings.sandbox_timeout_seconds = 3
        try:
            with self.assertRaises(SandboxError):
                run_submission(
                    "def two_sum(nums, target):\n    while True:\n        pass\n",
                    PROBLEMS["two-sum"]["test_cases"],
                    "def two_sum(nums, target):",
                )
        finally:
            settings.sandbox_timeout_seconds = original


if __name__ == "__main__":
    unittest.main()
