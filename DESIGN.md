# ParScript (Par Prompt) — Design Doc

Website that lets users train on algorithmic coding problems with different levels of AI
integration/assistance. This doc is the shared source of truth for the 8-hour build tonight —
read section 2 first to know what's actually in scope.

## 1. Overview

Par Prompt is a LeetCode-style trainer for efficient AI-assisted coding. Users solve algorithmic
problems by prompting an LLM agent instead of writing code by hand. The core metric is **token
efficiency**: total input + output tokens used, measured against a per-problem "par" target, with
completion time as a tiebreaker. After a solution passes, an AI reviewer comments on how the code
could be improved.

## 2. Tonight's scope (8-hour build) vs. explicitly cut

**In scope tonight:**
- Full prompt-engineering mode only (user prompts an LLM, LLM writes code, user can edit before
  submitting).
- Python-only submissions.
- GitHub auth via Supabase, with a username-onboarding step.
- Problem list (difficulty filter, par tokens shown) + problem workspace + per-problem
  leaderboard.
- Every submit click persisted as an `attempts` row (pass or fail).
- AI review comment shown after a passing submission.
- Basic personal metrics page: totals solved, avg tokens-vs-par ratio (overall + by difficulty),
  history table of past submissions.

**Explicitly cut tonight (stretch goals, do not build first):**
- AI-assistant mode and no-AI mode.
- Handicap system.
- Global/overall leaderboard (aggregating across problems).
- Trend chart on the personal metrics page.
- Multi-language support (Python only for now).
- Resuming an in-progress chat/code session after a page refresh.

If time remains after the above is working end-to-end, pick from the cut list in that order.

## 3. Tech stack

- **Frontend:** React + Vite (plain, no Next.js), client-side routing via react-router.
- **Backend:** FastAPI (Python).
- **DB + Auth:** Supabase (Postgres, GitHub OAuth).
- **LLM:** OpenAI API, a cheap model (e.g. gpt-5-nano) for solving; a cheap call for the
  post-pass review comment too.
- **Code execution:** Docker, a single generic Python sandbox image, one `docker run` per
  submission (no container pool — startup latency is acceptable for demo scale).

## 4. Data model (Supabase/Postgres)

**`profiles`**
- `id` (= `auth.users.id`), `username`, `created_at`
- Row created on first login, right after the username-onboarding step.

**`problems`**
- `id`, `slug`, `title`, `description`, `difficulty` (`easy` | `medium` | `hard`)
- `par_tokens` (int) — manually set per problem at seed time, no auto-computation tonight.
- `function_signature` (text), `starter_code` (text)
- `test_cases` (jsonb) — array of `{input, expected_output}`. No hidden test cases tonight; all
  are visible to the user.
- Seed 2–3 problems by hand before the demo (e.g. Two Sum, Valid Parentheses, Reverse Linked
  List) with test cases and par values.

**`attempts`**
- `id`, `user_id`, `problem_id`, `code`, `input_tokens`, `output_tokens`, `elapsed_seconds`
- `test_results` (jsonb, per-test pass/fail), `passed` (bool), `created_at`
- **One row is inserted per Submit click, never updated** — this is the full history of every
  run, pass or fail.

**`submissions`**
- `id`, `attempt_id` (FK → the winning attempt), `user_id`, `problem_id`
- `total_input_tokens`, `total_output_tokens`, `elapsed_seconds`, `created_at`
- Inserted once, the first time a user passes a given problem. Leaderboard and personal metrics
  both read from this table.
- **Simplification:** only the first pass counts. Re-solving an already-passed problem does not
  create a new leaderboard entry tonight.

## 5. Backend API (FastAPI)

- `POST /chat` — body `{problem_id, message_history}` → calls OpenAI, returns
  `{reply, code, input_tokens, output_tokens}` for that call. The frontend accumulates tokens
  client-side across calls for the live counter. Token counts are trusted client-side tonight —
  no server-side session ledger.
- `POST /submit` — body `{problem_id, code, input_tokens, output_tokens, elapsed_seconds}` → runs
  the code in the Docker sandbox against `problems.test_cases`, inserts an `attempts` row, and if
  all tests pass and no `submissions` row exists yet for this user+problem, inserts one. Returns
  `{passed, test_results, attempt_id}`.
- `POST /review` — body `{problem_id, code}` → one-off OpenAI call for improvement comments,
  returned directly (not persisted tonight).
- `GET /problems` — list, filterable by difficulty.
- `GET /problems/{id}` — full detail incl. `starter_code`, `test_cases`.
- `GET /leaderboard/{problem_id}` — submissions for that problem, ordered by total tokens
  ascending, tiebreak `elapsed_seconds` ascending, joined to `profiles.username`.
- `GET /me/metrics` — aggregate stats + history table for the logged-in user, scoped to
  `submissions`.

## 6. Docker sandbox contract

- One generic Python 3 image. The backend writes a temp file per submission combining: a runner
  harness + the submitted code, which loops over `test_cases`, calls the function, compares
  actual vs. expected, and prints a JSON result line.
- Run via `docker run --rm --network none --memory 256m --cpus 0.5` with a wall-clock timeout
  (e.g. `timeout 10s`, or a Python-side subprocess timeout) so a bad or looping LLM solution can't
  hang a submission.
- The backend parses the JSON result into a per-test pass/fail list plus an overall `passed`
  bool.
- This timeout/resource cap is a stability requirement, not a security hardening step — it exists
  so one bad submission can't hang the demo, not to sandbox against a malicious user.

## 7. Frontend pages/components

- **Login/onboarding:** Supabase GitHub auth button; username prompt on first login, writes a
  `profiles` row.
- **Problem list:** cards/table filtered by difficulty, showing difficulty tag + par tokens.
- **Problem workspace:** split view — problem description panel next to a chat panel with an
  editable code panel. Live token counter (accumulated client-side) shown against par. Timer
  running since the first chat message. Submit button calls `/submit`; failing test cases shown
  inline; user can keep chatting/editing and resubmit (each resubmit is a new `attempts` row).
- **Results view:** on pass, show finalized totals and call `/review` to display the AI's
  comments.
- **Leaderboard:** per-problem table — tokens ascending, time tiebreak, username.
- **Personal metrics page:** totals solved, avg tokens-vs-par ratio overall and by difficulty,
  history table from `/me/metrics` (problem, tokens, par, time, pass/fail). No trend chart
  tonight.

## 8. Team split (3 people, parallelizable)

Work in separate top-level directories (`/frontend`, `/backend`) to minimize merge conflicts on
one branch.

1. **Backend + OpenAI + sandbox** — `POST /chat`, `POST /submit`, `POST /review`, the Docker
   sandbox runner script.
2. **Supabase schema + auth + data endpoints** — table creation, GitHub OAuth wiring, seeding 2–3
   problems, `GET /problems*`, `GET /leaderboard/{id}`, `GET /me/metrics`.
3. **Frontend** — all pages/components in section 7, built against the API contract in section 5
   so backend and frontend can proceed in parallel.

## 9. Assumptions / simplifications (call these out, don't silently relitigate them)

- Token counts for the live counter are client-reported and trusted; no server-side session
  ledger tonight.
- No resume of in-progress chat/code after a page refresh — session state lives in React state
  only.
- Only the first passing submission per user+problem counts (no "best of" re-solving).
- No hidden test cases — all test cases are visible to the user.
- Par values are manually authored per seeded problem, not auto-computed.
