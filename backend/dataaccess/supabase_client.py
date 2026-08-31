"""Supabase client factory — one place to build the configured client
so every dataaccess module shares connection setup (uses settings from config.py).

The backend talks to Supabase with the service-role key, which bypasses RLS.
Never expose this client or its key to the frontend.

Owner: Supabase person (DESIGN.md §8.1).
"""

from functools import lru_cache

from supabase import Client, create_client

from config import settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a process-wide Supabase client authenticated with the service key."""
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set (see backend/.env.example)"
        )
    return create_client(settings.supabase_url, settings.supabase_service_key)
