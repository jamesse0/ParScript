"""In-container harness for the 'system_design' problem category (test_kind='pytest').

Runs INSIDE the sandbox image, not in the API process. services/sandbox_runner.py
writes three files into the per-run temp dir mounted over /sandbox:

    solution.py         <- the submitted code
    test_solution.py    <- the problem's hidden pytest module (problems.test_file)
    pytest_harness.py    <- this file

then runs `docker run ... parscript-sandbox python pytest_harness.py`.

It runs pytest against test_solution.py and prints a SINGLE JSON line to stdout,
in the same envelope sandbox/runner.py uses so services/sandbox_runner.py parses
both paths identically:

    {"passed": <bool>,
     "results": [{"input": "<test name>", "expected_output": null,
                  "actual_output": null, "passed": <bool>, "error": "<msg>"}, ...]}

Only the short failure message (the "E  AssertionError: ..." line -- i.e. the
author's assert message, not the test body) is ever included, with filesystem
paths stripped. The test source is never emitted: the solver may see which
tests failed, not how they are written.
"""

import json
import re
import sys

import pytest

# Any absolute path -- keeps the failure reason (assert message, exception type)
# while removing file locations that could hint at the test source.
_PATH_RE = re.compile(r"/[^\s:)'\"]+")


def _strip_paths(text: str) -> str:
    return _PATH_RE.sub("<path>", text)


def _short_message(longrepr) -> str:
    """A one-line failure summary with no test source and no paths."""
    msg = None
    crash = getattr(longrepr, "reprcrash", None)
    if crash is not None:
        msg = getattr(crash, "message", None)
    if not msg:
        text = str(longrepr) if longrepr is not None else ""
        err_lines = [ln for ln in text.splitlines() if ln.lstrip().startswith("E ")]
        if err_lines:
            msg = err_lines[-1].lstrip()[1:].strip()
        else:
            stripped = [ln for ln in text.splitlines() if ln.strip()]
            msg = stripped[-1].strip() if stripped else "test failed"
    return _strip_paths(msg)[:300]


class _Collector:
    """Records one result entry per test node (and per collection failure)."""

    def __init__(self) -> None:
        self.results: list[dict] = []
        self._seen: set[str] = set()

    def _add(self, name: str, passed: bool, error: str | None) -> None:
        if name in self._seen:
            return
        self._seen.add(name)
        entry = {
            "input": name,
            "expected_output": None,
            "actual_output": None,
            "passed": passed,
        }
        if error:
            entry["error"] = error
        self.results.append(entry)

    def pytest_collectreport(self, report) -> None:
        if report.failed:
            name = report.nodeid or "collection"
            self._add(
                f"collection error ({name})",
                False,
                _short_message(report.longrepr)
                + " -- check the class/method names match the signature exactly",
            )

    def pytest_runtest_logreport(self, report) -> None:
        # 'call' is the test body; a failed 'setup' means a fixture blew up
        # before the test ran -- report that too. Ignore passing setup/teardown.
        if report.when == "call":
            self._add(report.nodeid, report.passed, None if report.passed else _short_message(report.longrepr))
        elif report.when in ("setup", "teardown") and report.failed:
            self._add(f"{report.nodeid} ({report.when})", False, _short_message(report.longrepr))


def main() -> None:
    collector = _Collector()
    try:
        pytest.main(
            [
                "-q",
                "--no-header",
                "-p", "no:cacheprovider",
                "--basetemp=/tmp/pt",
                "test_solution.py",
            ],
            plugins=[collector],
        )
    except Exception as e:  # noqa: BLE001 - never let the harness itself 500 the run
        collector.results.append(
            {
                "input": "harness error",
                "expected_output": None,
                "actual_output": None,
                "passed": False,
                "error": _strip_paths(f"{type(e).__name__}: {e}")[:300],
            }
        )

    if not collector.results:
        collector.results.append(
            {
                "input": "no tests collected",
                "expected_output": None,
                "actual_output": None,
                "passed": False,
                "error": "the grader collected no tests",
            }
        )

    passed = all(r["passed"] for r in collector.results)
    print(json.dumps({"passed": passed, "results": collector.results}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"passed": False, "error": f"pytest harness crashed: {e}", "results": []}))
        sys.exit(1)
