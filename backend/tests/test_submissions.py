"""Tests for dataaccess/submissions.py leaderboard + metrics, including the
prompt/manual `mode` split. Runs offline against a fake Supabase client that
applies `.eq(...)` filters so mode scoping is actually exercised.
"""

import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import dataaccess.submissions as S  # noqa: E402


class _Resp:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, rows):
        self._rows = rows
        self._filters = []

    def select(self, *a, **k):
        return self

    def order(self, *a, **k):
        return self

    def eq(self, col, val):
        self._filters.append((col, val))
        return self

    def execute(self):
        rows = self._rows
        for col, val in self._filters:
            rows = [r for r in rows if r.get(col) == val]
        return _Resp(rows)


class _FakeSupabase:
    def __init__(self, rows):
        self._rows = rows

    def table(self, _name):
        return _Query(list(self._rows))


def use_rows(rows):
    S.get_supabase = lambda: _FakeSupabase(rows)


def sub(**over):
    row = {
        "user_id": "u1",
        "problem_id": 1,
        "passed": True,
        "mode": "prompt",
        "input_tokens": 100,
        "output_tokens": 50,
        "elapsed_seconds": 60,
        "created_at": "2026-08-31T10:00:00Z",
        "profiles": {"username": "u1"},
        "problems": {"title": "P1", "par_tokens": 300, "difficulty": "easy"},
    }
    row.update(over)
    return row


class TestLeaderboardModeSplit(unittest.TestCase):
    def test_prompt_leaderboard_excludes_manual_and_ranks_by_tokens(self):
        use_rows([
            sub(user_id="a", mode="prompt", input_tokens=100, output_tokens=50, elapsed_seconds=90, profiles={"username": "a"}),
            sub(user_id="b", mode="prompt", input_tokens=40, output_tokens=20, elapsed_seconds=200, profiles={"username": "b"}),
            sub(user_id="c", mode="manual", input_tokens=0, output_tokens=0, elapsed_seconds=5, profiles={"username": "c"}),
        ])
        rows = S.leaderboard_for_problem(1, "prompt")
        self.assertEqual([r["username"] for r in rows], ["b", "a"])  # fewer tokens first
        self.assertNotIn("c", [r["username"] for r in rows])
        self.assertNotIn("_rank_key", rows[0])

    def test_manual_leaderboard_only_manual_and_ranks_by_time(self):
        use_rows([
            sub(user_id="a", mode="manual", elapsed_seconds=120, profiles={"username": "a"}),
            sub(user_id="b", mode="manual", elapsed_seconds=45, profiles={"username": "b"}),
            sub(user_id="z", mode="prompt", elapsed_seconds=1, profiles={"username": "z"}),
        ])
        rows = S.leaderboard_for_problem(1, "manual")
        self.assertEqual([r["username"] for r in rows], ["b", "a"])  # faster first
        self.assertNotIn("z", [r["username"] for r in rows])

    def test_best_run_per_user(self):
        use_rows([
            sub(user_id="a", mode="manual", elapsed_seconds=200, created_at="2026-08-31T09:00:00Z", profiles={"username": "a"}),
            sub(user_id="a", mode="manual", elapsed_seconds=30, created_at="2026-08-31T11:00:00Z", profiles={"username": "a"}),
        ])
        rows = S.leaderboard_for_problem(1, "manual")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["elapsed_seconds"], 30.0)

    def test_default_mode_is_prompt(self):
        use_rows([
            sub(user_id="a", mode="prompt", profiles={"username": "a"}),
            sub(user_id="c", mode="manual", profiles={"username": "c"}),
        ])
        rows = S.leaderboard_for_problem(1)
        self.assertEqual([r["username"] for r in rows], ["a"])


class TestMetricsExcludesManual(unittest.TestCase):
    def test_manual_submission_does_not_count(self):
        use_rows([
            sub(problem_id=1, mode="prompt", input_tokens=100, output_tokens=50),   # ratio 150/300
            sub(problem_id=2, mode="manual", input_tokens=0, output_tokens=0,
                problems={"title": "P2", "par_tokens": 400, "difficulty": "hard"}),
        ])
        m = S.metrics_for_user("u1")
        self.assertEqual(m["total_solved"], 1)
        self.assertEqual([h["problem_title"] for h in m["history"]], ["P1"])
        self.assertNotIn("hard", m["avg_tokens_vs_par_by_difficulty"])
        self.assertAlmostEqual(m["avg_tokens_vs_par"], 150 / 300)

    def test_manual_only_solve_is_invisible(self):
        use_rows([sub(problem_id=5, mode="manual", input_tokens=0, output_tokens=0)])
        m = S.metrics_for_user("u1")
        self.assertEqual(m["total_solved"], 0)
        self.assertEqual(m["history"], [])


class TestGlobalLeaderboard(unittest.TestCase):
    def test_ranks_by_handicap_ascending(self):
        use_rows([
            # user a: 150/300 on P1 -> handicap 0.5
            sub(user_id="a", problem_id=1, input_tokens=100, output_tokens=50,
                profiles={"username": "a"}, problems={"title": "P1", "par_tokens": 300, "difficulty": "easy"}),
            sub(user_id="a", problem_id=2, input_tokens=100, output_tokens=100,
                profiles={"username": "a"}, problems={"title": "P2", "par_tokens": 400, "difficulty": "easy"}),
            sub(user_id="a", problem_id=3, input_tokens=100, output_tokens=100,
                profiles={"username": "a"}, problems={"title": "P3", "par_tokens": 400, "difficulty": "easy"}),
            # user b: worse ratios, same solve count
            sub(user_id="b", problem_id=1, input_tokens=200, output_tokens=200,
                profiles={"username": "b"}, problems={"title": "P1", "par_tokens": 300, "difficulty": "easy"}),
            sub(user_id="b", problem_id=2, input_tokens=200, output_tokens=200,
                profiles={"username": "b"}, problems={"title": "P2", "par_tokens": 400, "difficulty": "easy"}),
            sub(user_id="b", problem_id=3, input_tokens=200, output_tokens=200,
                profiles={"username": "b"}, problems={"title": "P3", "par_tokens": 400, "difficulty": "easy"}),
        ])
        rows = S.global_leaderboard(min_solves=3)
        self.assertEqual([r["username"] for r in rows], ["a", "b"])
        self.assertTrue(rows[0]["handicap"] < rows[1]["handicap"])
        self.assertEqual(rows[0]["problems_solved"], 3)

    def test_excludes_users_below_min_solves(self):
        use_rows([
            sub(user_id="a", problem_id=1, profiles={"username": "a"}),
            sub(user_id="a", problem_id=2, profiles={"username": "a"},
                problems={"title": "P2", "par_tokens": 300, "difficulty": "easy"}),
        ])
        rows = S.global_leaderboard(min_solves=3)
        self.assertEqual(rows, [])

    def test_best_run_per_problem_counts_not_every_attempt(self):
        use_rows([
            sub(user_id="a", problem_id=1, input_tokens=200, output_tokens=100,
                created_at="2026-08-31T09:00:00Z", profiles={"username": "a"}),
            sub(user_id="a", problem_id=1, input_tokens=50, output_tokens=25,
                created_at="2026-08-31T10:00:00Z", profiles={"username": "a"}),
            sub(user_id="a", problem_id=2, profiles={"username": "a"},
                problems={"title": "P2", "par_tokens": 300, "difficulty": "easy"}),
            sub(user_id="a", problem_id=3, profiles={"username": "a"},
                problems={"title": "P3", "par_tokens": 300, "difficulty": "easy"}),
        ])
        rows = S.global_leaderboard(min_solves=3)
        self.assertEqual(rows[0]["problems_solved"], 3)
        self.assertAlmostEqual(rows[0]["handicap"], (75 / 300 + 150 / 300 + 150 / 300) / 3)

    def test_manual_submissions_excluded(self):
        use_rows([
            sub(user_id="a", problem_id=1, mode="manual", profiles={"username": "a"}),
            sub(user_id="a", problem_id=2, mode="manual", profiles={"username": "a"}),
            sub(user_id="a", problem_id=3, mode="manual", profiles={"username": "a"}),
        ])
        rows = S.global_leaderboard(min_solves=3)
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
