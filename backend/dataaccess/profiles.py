"""profiles table (DESIGN.md §4): id (= auth.users.id), username, created_at.
Row created on first login, right after the username-onboarding step.

Owner: Supabase person (DESIGN.md §8.1).
"""

from postgrest.exceptions import APIError

from dataaccess.supabase_client import get_supabase


class UsernameTakenError(Exception):
    """Raised when a username (or the profile) already exists."""


def get_profile(user_id: str) -> dict | None:
    """The profile row for this auth user, or None if they haven't onboarded."""
    rows = (
        get_supabase()
        .table("profiles")
        .select("id, username, created_at")
        .eq("id", user_id)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


def create_profile(user_id: str, username: str) -> dict:
    """Insert the profile row. Raises UsernameTakenError on any unique conflict
    (either the username is in use, or this user already has a profile)."""
    try:
        rows = (
            get_supabase()
            .table("profiles")
            .insert({"id": user_id, "username": username})
            .execute()
            .data
        )
    except APIError as exc:
        if exc.code == "23505":  # unique_violation
            raise UsernameTakenError(username) from exc
        raise
    return rows[0]
