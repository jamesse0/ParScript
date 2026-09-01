"""Fill the DB with believable placeholder activity for demos / screenshots.

Creates a pool of demo users and, for every problem, 5-8 passing 'prompt'
submissions whose token totals are clustered around that problem's par_tokens
(some under, some over), plus the occasional worse/failed run for texture.

Everything it creates is tagged by a shared email prefix so `--purge` can wipe
it cleanly (deleting the auth user cascades to profiles + submissions).

Usage (from backend/):
    python db/seed_demo_data.py                 # ~10 users, 5-8 entries/problem
    python db/seed_demo_data.py --users 12 --min 6 --max 9 --seed 7
    python db/seed_demo_data.py --purge         # delete demo users + their data, exit

Safe to re-run: it wipes the demo users' existing submissions first, so the
resulting state is deterministic for a given --seed.
"""

import argparse
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dataaccess.supabase_client import get_supabase  # noqa: E402

PROBLEMS_FILE = Path(__file__).resolve().parent / "problems.json"

# Shared marker: every demo user's email is DEMO_PREFIX + n + DEMO_DOMAIN.
DEMO_PREFIX = "parscript-demo-"
DEMO_DOMAIN = "@parscript-demo.dev"
DEMO_PASSWORD = "demo-user-pw"  # noqa: S105 - throwaway local demo creds

# Problem-agnostic prompt phrasings (the real system prompt never sees the task
# spec, so demo users "describe" it themselves). ~70% of passing runs get an
# attempt built from these; the rest stay trace-less (hand-edited).
FIRST_TURNS = [
    "Write a function matching the signature that returns the expected result. "
    "For empty input, return an empty result of the same type rather than raising.",
    "Aim for a single pass over the input. Use a dict/hash map to remember what "
    "you've already seen and check for the complement as you go.",
    "Use a greedy approach: take the locally optimal choice at each step. You can "
    "assume the input is always valid.",
    "Solve this with bottom-up dynamic programming — build a table and return the "
    "last entry. Keep memory to O(n).",
    "Keep it simple and readable; a straightforward nested loop is fine here, "
    "correctness matters more than speed.",
    "Recursion with memoization. Base case is an empty or single-element input; "
    "cache on the arguments.",
    "Sort the input ascending first, then walk it comparing each adjacent pair.",
    "Return indices, not values, and put them in ascending order. Exactly one "
    "valid answer exists for every input.",
    "Treat it as a stack: push on open, pop and match on close. The input is "
    "valid iff the stack is empty at the end.",
    "Two pointers, one from each end; move the pointer at the smaller value "
    "inward until they meet.",
]
FOLLOWUPS = [
    "That raises on empty input — return 0 or an empty list there instead.",
    "Make it O(n) instead of O(n^2), the nested loop is too slow.",
    "Duplicates in the input break it; handle those and keep the rest the same.",
    "Don't mutate the caller's argument — copy it first.",
    "The output order is wrong, sort ascending before returning.",
    "If there's no valid answer, return -1 rather than None.",
    "Drop the helper function and inline it, it's only used once.",
]

HANDLES = [
    "nova_dev", "quillbot", "byte_baron", "async_annie", "loop_luis",
    "prompt_pete", "regex_rex", "tokenwise", "bigO_bri", "lambda_lena",
    "greedy_gwen", "cache_cassie", "eager_eli", "heap_hana", "static_stan",
]


def _demo_email(i: int) -> str:
    return f"{DEMO_PREFIX}{i:02d}{DEMO_DOMAIN}"


def _find_demo_users(sb) -> list:
    return [u for u in sb.auth.admin.list_users() if (u.email or "").startswith(DEMO_PREFIX)]


def purge(sb) -> int:
    users = _find_demo_users(sb)
    for u in users:
        # cascade: auth.users -> profiles -> attempts/submissions
        sb.auth.admin.delete_user(u.id)
        print(f"  deleted  {u.email}")
    print(f"purged {len(users)} demo user(s)")
    return 0


def ensure_users(sb, count: int) -> list[tuple[str, str]]:
    """Return [(user_id, username)] for `count` demo users, creating any missing."""
    existing = {u.email: u.id for u in _find_demo_users(sb)}
    out: list[tuple[str, str]] = []
    for i in range(count):
        email = _demo_email(i)
        username = HANDLES[i % len(HANDLES)]
        uid = existing.get(email)
        if uid is None:
            created = sb.auth.admin.create_user(
                {"email": email, "password": DEMO_PASSWORD, "email_confirm": True}
            )
            uid = created.user.id
            print(f"  created  {email}  ({username})")
        sb.table("profiles").upsert({"id": uid, "username": username}, on_conflict="id").execute()
        out.append((uid, username))
    return out


def _load_problems(sb) -> list[dict]:
    db_rows = (
        sb.table("problems").select("id, slug, par_tokens, test_kind").order("id").execute().data
        or []
    )
    by_slug = {p["slug"]: p for p in json.loads(PROBLEMS_FILE.read_text())}
    for row in db_rows:
        row["test_cases"] = by_slug.get(row["slug"], {}).get("test_cases") or []
    return db_rows


def _test_results(problem: dict, passed: bool) -> list[dict]:
    if problem["test_kind"] == "pytest":
        base = [
            {"input": f"{problem['slug']}::test_{n}", "expected_output": None,
             "actual_output": None, "passed": True}
            for n in range(1, 5)
        ]
    else:
        base = [
            {"input": tc.get("input"), "expected_output": tc.get("expected_output"),
             "actual_output": tc.get("expected_output"), "passed": True}
            for tc in problem["test_cases"][:4]
        ] or [{"input": None, "expected_output": True, "actual_output": True, "passed": True}]
    if not passed:
        base[-1] = {**base[-1], "passed": False, "actual_output": None,
                    "error": "AssertionError: demo failure"}
    return base


def _split_tokens(total: int) -> tuple[int, int]:
    """A smaller user prompt + a larger model output (code + reasoning)."""
    inp = max(20, round(total * random.uniform(0.15, 0.33)))
    return inp, max(1, total - inp)


def _elapsed_for(output_tokens: int) -> float:
    # New timer semantics: cumulative time spent waiting on the model.
    secs = output_tokens * random.uniform(0.012, 0.035) + random.gauss(0, 4)
    return round(max(4.0, secs), 1)


def _iso(days_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def _make_attempt(problem: dict, uid: str, day: float, inp: int, out: int) -> dict:
    """A 1-3 turn chat whose message_history is what the prompt-trace endpoint
    surfaces (it keeps the user turns)."""
    turns = random.randint(1, 3)
    history = [{"role": "user", "content": random.choice(FIRST_TURNS)}]
    for _ in range(turns - 1):
        history.append({"role": "assistant", "content": "```python\n# ...\n```"})
        history.append({"role": "user", "content": random.choice(FOLLOWUPS)})
    return {
        "user_id": uid, "problem_id": problem["id"], "message_history": history,
        "reply": "```python\n# demo\n```",
        "code": f"# demo solution for {problem['slug']}\n",
        "input_tokens": max(1, inp // turns), "output_tokens": max(1, out // turns),
        "model": "gpt-5-nano", "created_at": _iso(day + 0.02),
    }


def build_rows(users: list[tuple[str, str]], problems: list[dict],
               lo: int, hi: int) -> list[dict]:
    rows: list[dict] = []
    for problem in problems:
        par = problem["par_tokens"] or 1500
        k = min(len(users), random.randint(lo, hi))
        for uid, _ in random.sample(users, k):
            # cluster around par: gaussian centred on 1.0x, tails on both sides
            factor = min(1.75, max(0.5, random.gauss(1.0, 0.22)))
            total = max(120, round(par * factor))
            inp, out = _split_tokens(total)
            best_day = random.uniform(0, 18)
            # every passing run carries its chat trace
            rows.append({
                "user_id": uid, "problem_id": problem["id"], "attempt_id": None,
                "_attempt": _make_attempt(problem, uid, best_day, inp, out),
                "code": f"# demo solution for {problem['slug']}\n",
                "test_results": _test_results(problem, True), "passed": True,
                "input_tokens": inp, "output_tokens": out,
                "elapsed_seconds": _elapsed_for(out), "mode": "prompt",
                "created_at": _iso(best_day),
            })
            # ~35%: an earlier, worse attempt (a failed run, or a costlier pass)
            if random.random() < 0.35:
                passed = random.random() < 0.55
                worse_total = round(total * random.uniform(1.12, 1.6))
                winp, wout = _split_tokens(worse_total)
                worse_day = best_day + random.uniform(0.5, 8)
                rows.append({
                    "user_id": uid, "problem_id": problem["id"], "attempt_id": None,
                    # give the earlier passing tries a trace too; failed ones look hand-run
                    "_attempt": _make_attempt(problem, uid, worse_day, winp, wout) if passed else None,
                    "code": f"# demo solution for {problem['slug']} (earlier try)\n",
                    "test_results": _test_results(problem, passed), "passed": passed,
                    "input_tokens": winp, "output_tokens": wout,
                    "elapsed_seconds": _elapsed_for(wout), "mode": "prompt",
                    "created_at": _iso(worse_day),
                })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--users", type=int, default=10)
    ap.add_argument("--min", type=int, default=5, dest="lo")
    ap.add_argument("--max", type=int, default=8, dest="hi")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--purge", action="store_true", help="delete demo users + their data, then exit")
    args = ap.parse_args()

    random.seed(args.seed)
    sb = get_supabase()

    if args.purge:
        return purge(sb)

    if args.lo > args.hi:
        print("error: --min must be <= --max", file=sys.stderr)
        return 1

    print(f"ensuring {args.users} demo users...")
    users = ensure_users(sb, args.users)

    demo_ids = [uid for uid, _ in users]
    # submissions FK attempts, so clear submissions first, then attempts.
    d_sub = sb.table("submissions").delete().in_("user_id", demo_ids).execute().data or []
    d_att = sb.table("attempts").delete().in_("user_id", demo_ids).execute().data or []
    print(f"cleared {len(d_sub)} demo submission(s), {len(d_att)} demo attempt(s)")

    problems = _load_problems(sb)
    rows = build_rows(users, problems, args.lo, args.hi)

    # phase 1: insert the chat attempts, link each back to its submission row
    with_attempt = [r for r in rows if r.get("_attempt")]
    for start in range(0, len(with_attempt), 100):
        chunk = with_attempt[start:start + 100]
        inserted = sb.table("attempts").insert([r["_attempt"] for r in chunk]).execute().data
        for r, ins in zip(chunk, inserted):
            r["attempt_id"] = ins["id"]
    for r in rows:
        r.pop("_attempt", None)

    # phase 2: the submissions
    for start in range(0, len(rows), 200):
        sb.table("submissions").insert(rows[start:start + 200]).execute()

    # summary
    by_problem: dict[int, list[int]] = {}
    for r in rows:
        if r["passed"]:
            by_problem.setdefault(r["problem_id"], []).append(r["input_tokens"] + r["output_tokens"])
    traced = sum(1 for r in rows if r.get("attempt_id"))
    print(f"\ninserted {len(rows)} submission(s) ({traced} with a prompt trace) "
          f"across {len(problems)} problems:")
    for p in problems:
        totals = sorted(by_problem.get(p["id"], []))
        if not totals:
            continue
        print(f"  {p['slug']:<34} par {p['par_tokens']:>5}  "
              f"{len(totals)} passes  tokens {totals[0]}–{totals[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
