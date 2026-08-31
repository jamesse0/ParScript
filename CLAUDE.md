# ParScript

Website that allows users to train on algorithmic coding problems with different levels of AI
integration/assistance.

Before making any implementation or architecture decisions, read [DESIGN.md](DESIGN.md) — it is
the source of truth for tonight's scope (what's in vs. explicitly cut), the tech stack, the data
model, the backend API contract, the Docker sandbox contract, and the team split. Follow it
instead of re-deriving these decisions from scratch, and don't build anything listed there as
cut/stretch before the in-scope MVP works end-to-end.

## Known issues (flagged during Docker-person implementation)

- **`problem_id` type mismatch:** `schemas.SubmitRequest.problem_id` is typed `str`, but
  `problems.id` is a Postgres `bigint`. The frontend must send `problem_id` as a string in the
  `POST /submit` body — an int gets rejected with a 422. Same likely applies anywhere else
  `problem_id` is sent in a request body; check against `schemas.py`, not the DB column type.
- **Python version:** the shared backend code (`config.py`, `schemas.py`, `dataaccess/*`,
  `deps.py`) uses `X | Y` union type syntax, which requires **Python 3.10+**. Check your local
  Python version before running the backend — `python3 --version`.
