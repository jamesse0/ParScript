"""Load coding problems from a JSON file into the `problems` table.

The JSON file is the definitive list: rows are upserted on `slug`, and any
`problems` row whose slug is NOT in the file is deleted (unless it still has
attempts/submissions referencing it, in which case it's kept and reported).

For `test_kind: "pytest"` problems, `test_file` is a path (relative to the JSON
file's directory) to a real `.py` pytest module. Its contents are read and
stored in the `problems.test_file` column at seed time.

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

# Always required, regardless of grading kind.
BASE_REQUIRED = {
    "slug",
    "title",
    "description",
    "difficulty",
    "par_tokens",
    "function_signature",
    "starter_code",
}
# Allowed but grading-kind-dependent (see _validate). `course_only` hides a
# problem from GET /problems -- it's only reachable through its course.
OPTIONAL_ALLOWED = {"test_kind", "test_cases", "test_file", "course_only"}
ALLOWED_DIFFICULTY = {"easy", "medium", "hard", "system_design"}
ALLOWED_TEST_KIND = {"io_pairs", "pytest"}


def _validate(problem: dict, index: int, base_dir: Path) -> None:
    slug = problem.get("slug", "?")
    missing = BASE_REQUIRED - problem.keys()
    if missing:
        raise ValueError(f"problem[{index}] ({slug}): missing {sorted(missing)}")
    extra = problem.keys() - BASE_REQUIRED - OPTIONAL_ALLOWED
    if extra:
        raise ValueError(f"problem[{index}] ({slug}): unknown fields {sorted(extra)}")
    if problem["difficulty"] not in ALLOWED_DIFFICULTY:
        raise ValueError(
            f"problem[{index}] ({slug}): difficulty must be one of {sorted(ALLOWED_DIFFICULTY)}"
        )
    if not isinstance(problem["par_tokens"], int):
        raise ValueError(f"problem[{index}] ({slug}): par_tokens must be an int")

    test_kind = problem.get("test_kind", "io_pairs")
    if test_kind not in ALLOWED_TEST_KIND:
        raise ValueError(
            f"problem[{index}] ({slug}): test_kind must be one of {sorted(ALLOWED_TEST_KIND)}"
        )

    if test_kind == "io_pairs":
        if "test_file" in problem:
            raise ValueError(f"problem[{index}] ({slug}): io_pairs problems must not set test_file")
        tcs = problem.get("test_cases")
        if not isinstance(tcs, list) or not tcs:
            raise ValueError(f"problem[{index}] ({slug}): test_cases must be a non-empty array")
        for j, tc in enumerate(tcs):
            if not isinstance(tc, dict) or "input" not in tc or "expected_output" not in tc:
                raise ValueError(
                    f"problem[{index}] ({slug}): test_cases[{j}] needs 'input' and 'expected_output'"
                )
    else:  # pytest
        tf = problem.get("test_file")
        if not isinstance(tf, str) or not tf.strip():
            raise ValueError(
                f"problem[{index}] ({slug}): pytest problems need test_file (a path to a .py pytest module)"
            )
        if not tf.endswith(".py"):
            raise ValueError(f"problem[{index}] ({slug}): test_file must be a path to a .py file, got {tf!r}")
        resolved = (base_dir / tf).resolve()
        if not resolved.is_file():
            raise ValueError(f"problem[{index}] ({slug}): test_file not found: {resolved}")
        if not resolved.read_text().strip():
            raise ValueError(f"problem[{index}] ({slug}): test_file is empty: {resolved}")
        if problem.get("test_cases"):
            raise ValueError(f"problem[{index}] ({slug}): pytest problems must not set test_cases")


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

    base_dir = path.resolve().parent
    for i, problem in enumerate(problems):
        _validate(problem, i, base_dir)

    # Inline each pytest module's source (test_file is a path in the JSON, the
    # column stores the actual code). Then normalize the grading columns across
    # io_pairs and pytest problems -- PostgREST bulk upsert needs uniform keys.
    for problem in problems:
        problem.setdefault("test_kind", "io_pairs")
        problem.setdefault("test_cases", None)
        problem.setdefault("course_only", False)
        if problem["test_kind"] == "pytest":
            problem["test_file"] = (base_dir / problem["test_file"]).resolve().read_text()
        problem.setdefault("test_file", None)

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
