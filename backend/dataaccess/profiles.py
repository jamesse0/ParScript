"""profiles table (DESIGN.md §4): id (= auth.users.id), username, created_at.
Row created on first login, right after the username-onboarding step.

Owner: Supabase person (DESIGN.md §8.1).
"""


def get_profile(user_id: str):
    raise NotImplementedError


def create_profile(user_id: str, username: str):
    raise NotImplementedError
