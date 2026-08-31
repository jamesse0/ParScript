"""In-container test harness (DESIGN.md §6). Runs INSIDE the sandbox image,
not in the API process.

Receives the submitted code + test_cases, loops over test_cases, calls the
target function, compares actual vs expected, and prints a SINGLE JSON line
to stdout for services/sandbox_runner.py to parse:

    {"passed": <bool>,
     "results": [{"input": ..., "expected_output": ...,
                  "actual_output": ..., "passed": <bool>}, ...]}

Owner: Docker person (DESIGN.md §8.2).
"""


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
