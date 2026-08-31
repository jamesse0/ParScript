"""Profile / username-onboarding endpoints (DESIGN.md §4 profiles, §7 onboarding).

Owner: Supabase person (DESIGN.md §8.1).

  GET  /me           -> the caller's profile, or 404 if they haven't onboarded
  POST /me/profile   -> create the profile row with a chosen username (first login)
"""

from fastapi import APIRouter, Depends, HTTPException

from dataaccess import profiles as profiles_dao
from dataaccess.profiles import UsernameTakenError
from deps import get_current_user
from schemas import MeResponse, OnboardRequest

router = APIRouter(tags=["profile"])


@router.get("/me", response_model=MeResponse)
async def get_me(user=Depends(get_current_user)):
    profile = profiles_dao.get_profile(user["id"])
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found; onboarding required")
    return profile


@router.post("/me/profile", response_model=MeResponse, status_code=201)
async def create_my_profile(body: OnboardRequest, user=Depends(get_current_user)):
    username = body.username.strip()
    if not (3 <= len(username) <= 30) or not username.replace("_", "").isalnum():
        raise HTTPException(
            status_code=422,
            detail="Username must be 3-30 characters: letters, digits, underscores",
        )
    if profiles_dao.get_profile(user["id"]) is not None:
        raise HTTPException(status_code=409, detail="Profile already exists")
    try:
        return profiles_dao.create_profile(user["id"], username)
    except UsernameTakenError:
        raise HTTPException(status_code=409, detail="Username is taken")
