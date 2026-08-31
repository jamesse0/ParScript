"""Shared FastAPI dependencies.

get_current_user: validate the Supabase JWT from the Authorization header
(HS256, signed with settings.supabase_jwt_secret) and return the caller's
identity. No DB call here -- routes that need the profile fetch it themselves
(dataaccess.profiles). First-login onboarding lives in routes/profile.py.

Owner: Supabase person (auth remit, DESIGN.md §8.1). File is shared -- coordinate
before changing the return shape.
"""

import jwt
from fastapi import Header, HTTPException, status

from config import settings

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Missing or invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """Return {"id": <auth.users.id>, "email": <str | None>} for the bearer token."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _UNAUTHENTICATED

    token = authorization.split(" ", 1)[1].strip()
    if not settings.supabase_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_SECRET is not configured",
        )

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError:
        raise _UNAUTHENTICATED

    user_id = payload.get("sub")
    if not user_id:
        raise _UNAUTHENTICATED

    return {"id": user_id, "email": payload.get("email")}
