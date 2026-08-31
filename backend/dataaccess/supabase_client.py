"""Supabase client factory — one place to build the configured client
so every dataaccess module shares connection setup (uses settings from config.py).

Owner: Supabase person (DESIGN.md §8.1).
"""


def get_supabase():
    """Return a configured Supabase client (service key)."""
    raise NotImplementedError
