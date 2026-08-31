"""Shared FastAPI dependencies.

get_current_user: validate the Supabase access token from the Authorization
header and return the caller's identity. No DB call here -- routes that need the
profile fetch it themselves (dataaccess.profiles). First-login onboarding lives
in routes/profile.py.

Supabase projects on JWT signing keys issue asymmetric tokens (ES256/RS256)
verified against the project JWKS; older projects use a shared HS256 secret
(settings.supabase_jwt_secret). Both are supported here.

Owner: Supabase person (auth remit, DESIGN.md §8.1). File is shared -- coordinate
before changing the return shape.
"""

import jwt
from fastapi import Depends, Header, HTTPException, status

from config import settings
from dataaccess.profiles import get_profile

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Missing or invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

_JWKS_URL = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json" if settings.supabase_url else ""
# Caches keys in-process and refetches when it sees an unknown kid.
_jwks_client = jwt.PyJWKClient(_JWKS_URL) if _JWKS_URL else None


def _decode(token: str) -> dict:
    """Verify signature + claims, returning the payload. Raises on any failure."""
    alg = jwt.get_unverified_header(token).get("alg", "")
    common = {"audience": "authenticated", "options": {"require": ["exp", "sub"]}}

    if alg == "HS256":
        if not settings.supabase_jwt_secret:
            raise jwt.InvalidTokenError("HS256 token but SUPABASE_JWT_SECRET is unset")
        return jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], **common)

    if _jwks_client is None:
        raise jwt.InvalidTokenError("asymmetric token but SUPABASE_URL is unset")
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(token, signing_key.key, algorithms=["ES256", "RS256"], **common)


async def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """Return {"id": <auth.users.id>, "email": <str | None>} for the bearer token."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _UNAUTHENTICATED

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = _decode(token)
    except jwt.PyJWKClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"could not fetch signing keys: {exc}",
        )
    except jwt.PyJWTError:
        raise _UNAUTHENTICATED

    return {"id": payload["sub"], "email": payload.get("email")}


async def require_profile(user: dict = Depends(get_current_user)) -> dict:
    """get_current_user + the user must have completed username onboarding.

    Use on routes that write rows owning a profiles FK (attempts, submissions),
    so a not-yet-onboarded caller gets a clean 403 instead of a DB FK 500.
    Returns {"id", "email", "username"}.
    """
    profile = get_profile(user["id"])
    if profile is None:
        raise HTTPException(status_code=403, detail="username onboarding required")
    return {**user, "username": profile["username"]}
