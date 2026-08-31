"""Load coding problems from a JSON file into the `problems` table.

Usage (from backend/):
    python db/seed_problems.py                # loads db/problems.json
    python db/seed_problems.py path/to.json   # loads a specific file

Idempotent: rows are upserted on `slug`, so re-running after editing the JSON
updates the existing problems in place. Run after the schema migration is applied.
"""

import json
import sys
from pathlib import Path

# Allow running as `python db/seed_problems.py` (cwd=backend/) or
# `python backend/db/seed_problems.py` (cwd=repo root).
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dataaccess.supabase_client import get_supabase  # noqa: E402

DEFAULT_FILE = Path(__file__).resolve().parent / "problems.json"

REQUIRED_FIELDS = {
    "slug",
    "title",
    "description",
    "difficulty",
    "par_tokens",
    "function_signature",
    "starter_code",
    "test_cases",
}
ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}


def _validate(problem: dict, index: int) -> None:
    missing = REQUIRED_FIELDS - problem.keys()
    if missing:
        raise ValueError(f"problem[{index}] ({problem.get('slug', '?')}): missing {sorted(missing)}")
    extra = problem.keys() - REQUIRED_FIELDS
    if extra:
        raise ValueError(f"problem[{index}] ({problem['slug']}): unknown fields {sorted(extra)}")
    if problem["difficulty"] not in ALLOWED_DIFFICULTY:
        raise ValueError(
            f"problem[{index}] ({problem['slug']}): difficulty must be one of {sorted(ALLOWED_DIFFICULTY)}"
        )
    if not isinstance(problem["par_tokens"], int):
        raise ValueError(f"problem[{index}] ({problem['slug']}): par_tokens must be an int")
    tcs = problem["test_cases"]
    if not isinstance(tcs, list) or not tcs:
        raise ValueError(f"problem[{index}] ({problem['slug']}): test_cases must be a non-empty array")
    for j, tc in enumerate(tcs):
        if not isinstance(tc, dict) or "input" not in tc or "expected_output" not in tc:
            raise ValueError(
                f"problem[{index}] ({problem['slug']}): test_cases[{j}] needs 'input' and 'expected_output'"
            )


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    if not path.exists():
        print(f"error: {path} not found", file=sys.stderr)
        return 1

    problems = json.loads(path.read_text())
    if not isinstance(problems, list) or not problems:
        print(f"error: {path} must contain a non-empty JSON array", file=sys.stderr)
        return 1

    for i, problem in enumerate(problems):
        _validate(problem, i)

    slugs = [p["slug"] for p in problems]
    if len(set(slugs)) != len(slugs):
        print("error: duplicate slug(s) in the JSON file", file=sys.stderr)
        return 1

    supabase = get_supabase()

    existing = (
        supabase.table("problems").select("slug").in_("slug", slugs).execute().data or []
    )
    existing_slugs = {row["slug"] for row in existing}

    supabase.table("problems").upsert(problems, on_conflict="slug").execute()

    for slug in slugs:
        print(f"  {'updated' if slug in existing_slugs else 'inserted'}  {slug}")
    print(f"done: {len(slugs)} problem(s) from {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
