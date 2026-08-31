# Docker sandbox — progress

Scope: `backend/sandbox/*`, `backend/services/sandbox_runner.py`, `backend/routes/submit.py`,
per [backend/BACKEND.md](../BACKEND.md) ownership boundaries.

## Done — verified against live infrastructure, not just in isolation

- **`sandbox/Dockerfile`** — generic `python:3.12-slim` image, non-root submission execution.
  Builds clean: `docker build -t parscript-sandbox backend/sandbox`.
- **`sandbox/runner.py`** — in-container harness. `services/sandbox_runner.py` splices submitted
  code + injected `__FUNCTION_NAME__`/`__TEST_CASES__` in at the marker, writes it out, and it's
  bind-mounted over `/sandbox` so the image's `CMD ["python", "runner.py"]` runs the combined
  script. Prints one JSON line: `{"passed": bool, "results": [{"input", "expected_output",
  "actual_output", "passed"}, ...]}` — matches `schemas.TestResult` and the `submissions.test_results`
  column exactly.
- **`services/sandbox_runner.py`** — `run_submission(code, test_cases, function_signature) ->
  (passed, test_results)`. Runs via `docker run --rm --network none --memory 256m --cpus 0.5`
  with `settings.sandbox_timeout_seconds`. Raises `SandboxError` only for infra failures
  (timeout, crash, unparseable output) — a failing submission is a normal return, not an
  exception.
- **`routes/submit.py`** — `POST /submit`. Reads `problems` via `dataaccess.problems.get_problem`,
  runs the sandbox, inserts one `submissions` row every call via
  `dataaccess.submissions.insert_submission` (pass or fail — `attempts` is chat.py's table now,
  not this route's; the data model diverges from the original DESIGN.md wording, see
  `supabase/migrations/0001_init.sql`'s header comment).

**Full round-trip test performed** (throwaway auth user + profile created via the Supabase admin
API, real JWT signed with the real `SUPABASE_JWT_SECRET`, real HTTP `POST /submit` against a
running `uvicorn` server):
- Real `two_sum` problem read from Supabase, correct solution run through the actual Docker
  sandbox, all 4 real test cases passed, one real `submissions` row written and read back.
- Wrong solution and an infinite-loop submission both verified separately (fails cleanly /
  caught by the 10s timeout) against the standalone `services.sandbox_runner` module.
- Test user, profile, and submission row all deleted afterward — DB left clean (confirmed 0
  profiles / 0 submissions after cleanup).
- Caught one real contract bug in passing: `schemas.SubmitRequest.problem_id` is typed `str`
  even though `problems.id` is a Postgres `bigint` — the frontend must send `problem_id` as a
  string. Endpoint correctly 422s on an int.

## Environment note (this machine only)

This laptop only had Python 3.9.6; the shared backend code (`config.py`, `schemas.py`,
`dataaccess/*`, `deps.py`) uses `X | Y` union syntax requiring 3.10+. Installed Python 3.12.10
via the official python.org package to fix. Worth checking other teammates'/the demo laptop's
Python version ahead of time for the same reason.

## Not done

- Nothing outstanding in this scope. `/submit` is implemented and proven against live Supabase +
  a live Docker sandbox.
- Not this role's scope, but noting for visibility: no one has logged in through the real
  GitHub-auth flow yet (0 real profiles as of this test), so `deps.get_current_user` has only
  been verified against a manually-signed JWT with the correct shape, not a token that actually
  came out of Supabase's OAuth flow.

## How to verify

```bash
docker build -t parscript-sandbox backend/sandbox
cd backend && uvicorn main:app --reload   # needs backend/.env filled in
# POST /submit with a real Authorization: Bearer <supabase JWT>
```
