"""Shared FastAPI dependencies.

get_current_user: validate the Supabase JWT from the Authorization header
(settings.supabase_jwt_secret) and return the caller's identity, e.g.
{"id": ..., "username": ...}. Also the hook point for first-login profile
creation (DESIGN.md §4 profiles, §7 onboarding).

STUB.
"""

from fastapi import Header


async def get_current_user(authorization: str | None = Header(default=None)):
    raise NotImplementedError
