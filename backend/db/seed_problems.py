"""Load coding problems from a JSON file into the `problems` table.

The JSON file is the definitive list: rows are upserted on `slug`, and any
`problems` row whose slug is NOT in the file is deleted (unless it still has
attempts/submissions referencing it, in which case it's kept and reported).

Usage (from backend/):
    python db/seed_problems.py                  # loads db/problems.json
    python db/seed_problems.py path/to.json     # loads a specific file
    python db/seed_problems.py --keep-extras    # upsert only, don't delete extras
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


def _prune_extras(supabase, keep_slugs: set[str]) -> None:
    """Delete problems whose slug isn't in the file, skipping any that still
    have attempts/submissions pointing at them."""
    rows = supabase.table("problems").select("id, slug").execute().data or []
    extras = [r for r in rows if r["slug"] not in keep_slugs]
    if not extras:
        return
    for row in extras:
        pid = row["id"]
        refs = (
            len(supabase.table("attempts").select("id").eq("problem_id", pid).limit(1).execute().data)
            + len(supabase.table("submissions").select("id").eq("problem_id", pid).limit(1).execute().data)
        )
        if refs:
            print(f"  kept     {row['slug']}  (has attempts/submissions -- not deleted)")
            continue
        supabase.table("problems").delete().eq("id", pid).execute()
        print(f"  deleted  {row['slug']}  (not in file)")


def main() -> int:
    args = sys.argv[1:]
    keep_extras = "--keep-extras" in args
    args = [a for a in args if a != "--keep-extras"]
    path = Path(args[0]) if args else DEFAULT_FILE
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

    if not keep_extras:
        _prune_extras(supabase, set(slugs))

    print(f"done: {len(slugs)} problem(s) from {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
