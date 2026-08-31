# Supabase setup — ParScript

Everything the backend needs from Supabase: the schema, the seed data, and GitHub OAuth.
The FastAPI backend connects with the **service-role key** (bypasses RLS); the frontend only
uses Supabase for auth.

## 1. Schema + seed

`migrations/0001_init.sql` is the whole schema (`profiles`, `problems`, `attempts`,
`submissions`, the `leaderboard_entries` view, RLS). Problem seed data is JSON, loaded by a
script — see `backend/db/problems.json` and `backend/db/seed_problems.py`.

### Option A — Supabase CLI (most repeatable)

```sh
# once, if supabase/ isn't a CLI project yet:
supabase init                        # keep the existing migrations/ folder

supabase link --project-ref <ref>    # from the dashboard URL
supabase db push                     # apply migrations/ to the linked project
#   ...or, against a local dev stack:  supabase db reset

cd backend && python db/seed_problems.py   # load / refresh the problems
```

`supabase db reset` re-runs every migration from scratch; the seed step is a separate
command because the problems live in JSON, not SQL.

### Option B — psql, no CLI

```sh
export SUPABASE_DB_URL="postgresql://postgres:<pw>@db.<ref>.supabase.co:5432/postgres"
backend/db/apply.sh          # runs the migration, then seed_problems.py
```

### Adding / editing problems later

Edit `backend/db/problems.json`, then re-run `python backend/db/seed_problems.py`. Rows are
upserted on `slug`, so it's safe to run repeatedly.

## 2. GitHub OAuth

1. GitHub → Settings → Developer settings → **OAuth Apps** → New OAuth App.
   - Homepage URL: `http://localhost:5173`
   - Authorization callback URL: `https://<ref>.supabase.co/auth/v1/callback`
2. Supabase dashboard → **Authentication → Providers → GitHub**: enable it, paste the
   Client ID and Client Secret.
3. Supabase dashboard → **Authentication → URL Configuration**: add `http://localhost:5173`
   (and later the deployed origin) to the redirect allowlist.
4. Frontend sign-in:

   ```js
   await supabase.auth.signInWithOAuth({ provider: 'github' })
   ```

   After redirect, the session's `access_token` is the JWT the frontend sends as
   `Authorization: Bearer <token>` to the backend. The backend verifies it with
   `SUPABASE_JWT_SECRET` (HS256, audience `authenticated`) — see `backend/deps.py`.

## 3. Onboarding flow

A Supabase login does **not** create a `profiles` row. On first login the frontend calls:

- `GET /me` → `404` means "not onboarded" → show the username prompt.
- `POST /me/profile {"username": "..."}` → creates the row (`201`), `409` if the name is taken.

## 4. Backend env

Copy `backend/.env.example` → `backend/.env` and fill in `SUPABASE_URL`,
`SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET` (dashboard → Project Settings → API), plus
`SUPABASE_DB_URL` if you use Option B.
