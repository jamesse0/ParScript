"""Tests for deps.get_current_user (Supabase JWT verification).

Offline tests cover the reject paths. The real-token test mints an actual
Supabase access token and is skipped unless:

    PARSCRIPT_OPENAI_TESTS=1   (reused flag; needs backend/.env Supabase keys)
"""

import asyncio
import os
import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import HTTPException  # noqa: E402

import deps  # noqa: E402

_REAL = os.environ.get("PARSCRIPT_OPENAI_TESTS") == "1"


def call(auth_header):
    return asyncio.run(deps.get_current_user(auth_header))


class TestRejects(unittest.TestCase):
    def test_missing_header(self):
        with self.assertRaises(HTTPException) as ctx:
            call(None)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_not_bearer(self):
        with self.assertRaises(HTTPException):
            call("Token abc.def.ghi")

    def test_garbage_token(self):
        with self.assertRaises(HTTPException) as ctx:
            call("Bearer not-a-jwt")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_hs256_forged_token_rejected(self):
        import jwt

        forged = jwt.encode(
            {"sub": "x", "aud": "authenticated", "exp": 9999999999},
            "wrong-secret",
            algorithm="HS256",
        )
        with self.assertRaises(HTTPException) as ctx:
            call(f"Bearer {forged}")
        self.assertEqual(ctx.exception.status_code, 401)


@unittest.skipUnless(_REAL, "set PARSCRIPT_OPENAI_TESTS=1 to verify a real Supabase token")
class TestRealToken(unittest.TestCase):
    def test_accepts_real_supabase_token(self):
        from supabase import create_client

        from config import settings

        admin = create_client(settings.supabase_url, settings.supabase_service_key)
        email = "parscript-authtest@example.com"
        try:
            created = admin.auth.admin.create_user(
                {"email": email, "password": "authtest-pw", "email_confirm": True}
            )
            uid = created.user.id
        except Exception as exc:  # noqa: BLE001
            if "already" not in str(exc).lower():
                raise
            uid = next(u for u in admin.auth.admin.list_users() if u.email == email).id

        # dedicated client just for sign-in -- never reused for table ops
        signer = create_client(settings.supabase_url, settings.supabase_service_key)
        token = signer.auth.sign_in_with_password(
            {"email": email, "password": "authtest-pw"}
        ).session.access_token

        try:
            result = call(f"Bearer {token}")
            self.assertEqual(result["id"], uid)
            self.assertEqual(result["email"], email)
        finally:
            admin.auth.admin.delete_user(uid)


if __name__ == "__main__":
    unittest.main()
