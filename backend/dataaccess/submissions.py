"""submissions table (DESIGN.md §4): attempt_id (FK -> winning attempt), user_id,
problem_id, total_input_tokens, total_output_tokens, elapsed_seconds, created_at.

Inserted once, the first time a user passes a given problem. Leaderboard and
personal metrics both read from here.

Owner: Supabase person (DESIGN.md §8.1); insert path called by routes/submit.py.
"""


def get_submission(user_id: str, problem_id: str):
    """The user's existing submission for this problem, or None."""
    raise NotImplementedError


def insert_submission(**fields):
    raise NotImplementedError


def leaderboard_for_problem(problem_id: str):
    """Rows ordered by total tokens asc, elapsed_seconds asc, joined to profiles.username."""
    raise NotImplementedError


def metrics_for_user(user_id: str):
    """Aggregates + history rows for GET /me/metrics."""
    raise NotImplementedError
