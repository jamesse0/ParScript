"""problems table reads (DESIGN.md §4): slug, title, description, difficulty,
par_tokens, function_signature, starter_code, test_cases (jsonb).

Shared by routes/problems.py (full detail) and routes/submit.py
(test_cases / function_signature only).

Owner: Supabase person (DESIGN.md §8.1).
"""


def list_problems(difficulty: str | None = None):
    raise NotImplementedError


def get_problem(problem_id: str):
    raise NotImplementedError
