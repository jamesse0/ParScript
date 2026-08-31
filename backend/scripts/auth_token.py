"""Mint a real Supabase access token for a throwaway test user.

There's no frontend yet, so GitHub OAuth can't run. This creates (or reuses) a
plain email/password user via the Admin API and signs in to get a genuine
Supabase JWT (aud "authenticated") -- the same kind of token the GitHub flow
will hand the frontend. Use it to exercise the authed endpoints:

    cd backend
    TOKEN=$(.venv/bin/python scripts/auth_token.py)
    curl -s localhost:8000/me -H "Authorization: Bearer $TOKEN"
    curl -s localhost:8000/me/profile -X POST -H "Authorization: Bearer $TOKEN" \\
         -H 'content-type: application/json' -d '{"username":"demo"}'

Flags:
    --email a@b.com     use a specific address (default: parscript-dev@example.com)
    --password pw        (default: parscript-dev-password)
    --print-user         also print the user id + email to stderr

This is a dev tool. It uses the service-role key from backend/.env and only ever
touches auth.users (test accounts), never app tables.
"""

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from supabase import create_client  # noqa: E402

from config import settings  # noqa: E402

DEFAULT_EMAIL = "parscript-dev@example.com"
DEFAULT_PASSWORD = "parscript-dev-password"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--print-user", action="store_true")
    args = parser.parse_args()

    if not settings.supabase_url or not settings.supabase_service_key:
        print("SUPABASE_URL / SUPABASE_SERVICE_KEY missing from backend/.env", file=sys.stderr)
        return 1

    client = create_client(settings.supabase_url, settings.supabase_service_key)

    # Create the user if it doesn't exist yet; ignore "already registered".
    try:
        client.auth.admin.create_user(
            {
                "email": args.email,
                "password": args.password,
                "email_confirm": True,
            }
        )
    except Exception as exc:  # noqa: BLE001 - any "already exists" shape is fine
        if "already" not in str(exc).lower() and "registered" not in str(exc).lower():
            print(f"create_user failed: {exc}", file=sys.stderr)
            return 1

    session = client.auth.sign_in_with_password(
        {"email": args.email, "password": args.password}
    )
    if not session.session or not session.session.access_token:
        print("sign-in returned no session", file=sys.stderr)
        return 1

    if args.print_user:
        user = session.user
        print(f"user_id={user.id} email={user.email}", file=sys.stderr)

    print(session.session.access_token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
