# Backend structure (proposed)

FastAPI service. See [../DESIGN.md](../DESIGN.md) §4 (data model), §5 (API contract),
§6 (sandbox), §8 (team split). This file is the map; every `.py` below is a stub to be
filled in against the contract locked at the 15-minute sync.

## Layout

```
backend/
  main.py                  FastAPI app: CORS + include every router. `uvicorn main:app --reload`
  config.py                Env-driven settings (copy .env.example -> .env)
  deps.py                  Shared deps: get_current_user (validates Supabase JWT)
  schemas.py               Pydantic request/response models = the DESIGN.md §5 contract (DRAFT)
  requirements.txt
  .env.example

  routes/                  One file per endpoint group; each exposes `router = APIRouter()`
    problems.py            GET /problems, GET /problems/{id}          [Supabase person, §8.1]
    leaderboard.py         GET /leaderboard/{problem_id}              [Supabase person, §8.1]
    metrics.py             GET /me/metrics                            [Supabase person, §8.1]
    submit.py              POST /submit                               [Docker person, §8.2]
    chat.py                POST /chat                                 [Full-stack, §8.3]
    review.py              POST /review                               [Full-stack, §8.3]

  dataaccess/              Thin Supabase table wrappers, no HTTP concerns
    supabase_client.py     Configured client factory
    profiles.py            profiles table (created on first login)
    problems.py            problems table reads (shared: routes/problems + routes/submit)
    attempts.py            attempts table (one insert per Submit click, never updated)
    submissions.py         submissions table (first pass only) + leaderboard/metrics queries

  services/                External-system glue
    openai_client.py       OpenAI calls for /chat and /review        [Full-stack, §8.3]
    sandbox_runner.py      Drives `docker run` per submission, parses JSON result  [Docker, §8.2]

  sandbox/                 Runs inside the container, not the API process
    Dockerfile             Generic Python 3 image (build once)
    runner.py              In-container harness: loop test_cases, print one JSON result line
```

## Ownership boundaries (don't edit across them)

- **Supabase person:** `routes/problems.py`, `routes/leaderboard.py`, `routes/metrics.py`,
  all of `dataaccess/` + the Supabase project/schema/seed.
- **Docker person:** `sandbox/`, `services/sandbox_runner.py`, `routes/submit.py`.
  Only *reads* `problems`; writes `attempts`/`submissions` via `dataaccess/`.
- **Full-stack generalist:** `routes/chat.py`, `routes/review.py`, `services/openai_client.py`
  (plus all of `/frontend`). Calls the others' endpoints as a client.
- **Shared, agree before changing:** `schemas.py`, `main.py`, `config.py`, `deps.py`.

## Run

```
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in Supabase + OpenAI keys
uvicorn main:app --reload
```

Modules import top-level (`from config import settings`), so run from `backend/`.
