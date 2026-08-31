"""In-container test harness (DESIGN.md §6). Runs INSIDE the sandbox image,
not in the API process.

Receives the submitted code + test_cases, loops over test_cases, calls the
target function, compares actual vs expected, and prints a SINGLE JSON line
to stdout for services/sandbox_runner.py to parse:

    {"passed": <bool>,
     "results": [{"input": ..., "expected_output": ...,
                  "actual_output": ..., "passed": <bool>}, ...]}

Owner: Docker person (DESIGN.md §8.2).

This file as checked in is a TEMPLATE: services/sandbox_runner.py splices the
submitted code in at the marker below, appends __FUNCTION_NAME__ /
__TEST_CASES__ literals, and writes the result to a temp dir mounted over
/sandbox so `CMD ["python", "runner.py"]` runs the combined script.
"""

import json
import sys
import traceback


def _normalize_input(raw_input):
    """test_cases[i].input is stored as either a list of positional args or
    a dict of kwargs. Support both so problem authors have flexibility."""
    if isinstance(raw_input, dict):
        return [], raw_input
    if isinstance(raw_input, list):
        return raw_input, {}
    return [raw_input], {}


def main(function_name, test_cases):
    results = []
    all_passed = True

    try:
        func = globals()[function_name]
    except KeyError:
        print(json.dumps({
            "passed": False,
            "error": f"submitted code does not define a function named '{function_name}'",
            "results": [],
        }))
        return

    for case in test_cases:
        args, kwargs = _normalize_input(case.get("input"))
        expected_output = case.get("expected_output")
        entry = {"input": case.get("input"), "expected_output": expected_output}
        try:
            actual_output = func(*args, **kwargs)
            passed = actual_output == expected_output
            entry["actual_output"] = actual_output
            entry["passed"] = passed
            if not passed:
                all_passed = False
        except Exception as e:  # noqa: BLE001 - catch anything submitted code raises
            all_passed = False
            entry["actual_output"] = None
            entry["passed"] = False
            entry["error"] = f"{type(e).__name__}: {e}"
        results.append(entry)

    print(json.dumps({"passed": all_passed, "results": results}))


# ---SUBMITTED_CODE_INSERTION_POINT---
# services/sandbox_runner.py inserts the submitted code directly after this
# comment, then appends __FUNCTION_NAME__ / __TEST_CASES__ assignments.

if __name__ == "__main__":
    try:
        main(__FUNCTION_NAME__, __TEST_CASES__)  # noqa: F821 - injected by sandbox_runner.py
    except Exception:
        print(json.dumps({
            "passed": False,
            "error": "sandbox harness crashed",
            "traceback": traceback.format_exc(),
            "results": [],
        }))
        sys.exit(1)
