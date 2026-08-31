"""attempts table (DESIGN.md §4): user_id, problem_id, code, input_tokens,
output_tokens, elapsed_seconds, test_results (jsonb), passed, created_at.

One row inserted per Submit click, never updated — full history of every run.

Schema owned by Supabase person; written by routes/submit.py (Docker person, §8.2).
"""


def insert_attempt(**fields):
    """Insert one attempts row; return the new row (incl. id)."""
    raise NotImplementedError
