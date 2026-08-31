#!/usr/bin/env sh
# Apply the schema migration + seed the problems, without the Supabase CLI.
#
#   export SUPABASE_DB_URL="postgresql://postgres:...@db.<ref>.supabase.co:5432/postgres"
#   backend/db/apply.sh
#
# Prefer `supabase db reset` when the CLI is available (see supabase/README.md);
# this is the psql fallback.
set -eu

: "${SUPABASE_DB_URL:?set SUPABASE_DB_URL (see backend/.env.example)}"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)

echo "==> applying migration"
psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f "$REPO_ROOT/supabase/migrations/0001_init.sql"

echo "==> seeding problems"
cd "$SCRIPT_DIR/.."
python db/seed_problems.py

echo "==> done"
