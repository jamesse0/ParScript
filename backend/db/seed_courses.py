"""Load courses from db/courses.json into `courses` + `course_problems`.

Modeled on seed_problems.py: the JSON file is the source of truth. Courses are
upserted on `slug`; each course's `course_problems` rows are replaced to match
the file's `problems` order; a course in the DB but not the file is deleted
unless it has `course_completions` referencing it.

Every referenced problem slug must already exist AND be `course_only = true`
(run seed_problems.py first).

Usage (from backend/):
    python db/seed_courses.py
    python db/seed_courses.py --keep-extras
"""

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dataaccess.supabase_client import get_supabase  # noqa: E402

DEFAULT_FILE = Path(__file__).resolve().parent / "courses.json"
REQUIRED = {"slug", "title", "description", "problems"}


def _validate(course: dict, index: int) -> None:
    slug = course.get("slug", "?")
    missing = REQUIRED - course.keys()
    if missing:
        raise ValueError(f"course[{index}] ({slug}): missing {sorted(missing)}")
    extra = course.keys() - REQUIRED
    if extra:
        raise ValueError(f"course[{index}] ({slug}): unknown fields {sorted(extra)}")
    probs = course["problems"]
    if not isinstance(probs, list) or len(probs) < 2:
        raise ValueError(f"course[{index}] ({slug}): 'problems' must be a list of >= 2 slugs")
    if len(set(probs)) != len(probs):
        raise ValueError(f"course[{index}] ({slug}): duplicate problem slug in 'problems'")


def _prune_extras(sb, keep_slugs: set[str]) -> None:
    rows = sb.table("courses").select("id, slug").execute().data or []
    for row in rows:
        if row["slug"] in keep_slugs:
            continue
        refs = sb.table("course_completions").select("id").eq("course_id", row["id"]).limit(1).execute().data
        if refs:
            print(f"  kept     {row['slug']}  (has completions -- not deleted)")
            continue
        sb.table("courses").delete().eq("id", row["id"]).execute()
        print(f"  deleted  {row['slug']}  (not in file)")


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--keep-extras"]
    keep_extras = "--keep-extras" in sys.argv[1:]
    path = Path(args[0]) if args else DEFAULT_FILE
    if not path.exists():
        print(f"error: {path} not found", file=sys.stderr)
        return 1

    courses = json.loads(path.read_text())
    if not isinstance(courses, list) or not courses:
        print(f"error: {path} must contain a non-empty JSON array", file=sys.stderr)
        return 1
    for i, course in enumerate(courses):
        _validate(course, i)

    slugs = [c["slug"] for c in courses]
    if len(set(slugs)) != len(slugs):
        print("error: duplicate course slug(s) in the file", file=sys.stderr)
        return 1

    sb = get_supabase()

    # resolve every referenced problem slug -> id, enforcing course_only
    wanted = sorted({s for c in courses for s in c["problems"]})
    prob_rows = sb.table("problems").select("id, slug, course_only").in_("slug", wanted).execute().data or []
    by_slug = {r["slug"]: r for r in prob_rows}
    for slug in wanted:
        row = by_slug.get(slug)
        if row is None:
            print(f"error: problem '{slug}' not found -- run seed_problems.py first", file=sys.stderr)
            return 1
        if not row["course_only"]:
            print(f"error: problem '{slug}' is not course_only -- courses must use course-exclusive problems", file=sys.stderr)
            return 1

    existing = {r["slug"]: r["id"] for r in (sb.table("courses").select("id, slug").execute().data or [])}

    for course in courses:
        payload = {"slug": course["slug"], "title": course["title"], "description": course["description"]}
        sb.table("courses").upsert(payload, on_conflict="slug").execute()
        course_id = (
            sb.table("courses").select("id").eq("slug", course["slug"]).single().execute().data["id"]
        )
        sb.table("course_problems").delete().eq("course_id", course_id).execute()
        rows = [
            {"course_id": course_id, "problem_id": by_slug[s]["id"], "position": pos}
            for pos, s in enumerate(course["problems"])
        ]
        sb.table("course_problems").insert(rows).execute()
        verb = "updated" if course["slug"] in existing else "inserted"
        print(f"  {verb}  {course['slug']}  ({len(rows)} steps)")

    if not keep_extras:
        _prune_extras(sb, set(slugs))

    print(f"done: {len(slugs)} course(s) from {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
