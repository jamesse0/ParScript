"""Tests for dataaccess/courses.py -- course detail shaping, completion
verification (lower-total-wins), and course-leaderboard ordering. Offline, against
a small fake Supabase client that applies .eq/.in_ filters + .limit.
"""

import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import HTTPException  # noqa: E402

import dataaccess.courses as C  # noqa: E402


class _Resp:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, store, table):
        self._store = store
        self._table = table
        self._filters = []
        self._in = None
        self._limit = None

    def select(self, *a, **k):
        return self

    def order(self, *a, **k):
        return self

    def eq(self, col, val):
        self._filters.append((col, val))
        return self

    def in_(self, col, vals):
        self._in = (col, set(vals))
        return self

    def limit(self, n):
        self._limit = n
        return self

    def _rows(self):
        rows = list(self._store.get(self._table, []))
        for col, val in self._filters:
            rows = [r for r in rows if r.get(col) == val]
        if self._in:
            col, vals = self._in
            rows = [r for r in rows if r.get(col) in vals]
        if self._limit is not None:
            rows = rows[: self._limit]
        return rows

    def execute(self):
        return _Resp(self._rows())

    def single(self):
        rows = self._rows()
        return _Resp(rows[0] if rows else None)

    def upsert(self, row, **k):
        self._store.setdefault(self._table, []).append(row)
        return self

    def insert(self, rows, **k):
        self._store.setdefault(self._table, []).extend(rows if isinstance(rows, list) else [rows])
        return self

    def delete(self):
        return self


class _Fake:
    def __init__(self, store):
        self._store = store

    def table(self, name):
        return _Query(self._store, name)


def use(store):
    C.get_supabase = lambda: _Fake(store)


COURSE = {
    "id": 1,
    "slug": "c1",
    "title": "Course One",
    "description": "d",
    "course_problems": [
        {"position": 1, "problems": {"id": 20, "title": "S2", "par_tokens": 400}},
        {"position": 0, "problems": {"id": 10, "title": "S1", "par_tokens": 300}},
    ],
}


class TestGetCourse(unittest.TestCase):
    def test_steps_sorted_by_position_and_par_summed(self):
        use({"courses": [COURSE]})
        c = C.get_course("c1")
        self.assertEqual([s["position"] for s in c["steps"]], [0, 1])
        self.assertEqual([s["problem_id"] for s in c["steps"]], [10, 20])
        self.assertEqual(c["par_tokens"], 700)
        self.assertEqual(c["step_count"], 2)

    def test_unknown_course_is_none(self):
        use({"courses": []})
        self.assertIsNone(C.get_course("nope"))


class TestRecordCompletion(unittest.TestCase):
    def _sub(self, **over):
        row = {"id": "s1", "user_id": "u1", "problem_id": 10, "passed": True,
               "input_tokens": 100, "output_tokens": 50, "elapsed_seconds": 30}
        row.update(over)
        return row

    def test_happy_path_and_par(self):
        use({"courses": [COURSE], "submissions": [
            self._sub(id="a", problem_id=10, input_tokens=100, output_tokens=50),
            self._sub(id="b", problem_id=20, input_tokens=200, output_tokens=90),
        ], "course_completions": []})
        res = C.record_completion("u1", "c1", ["a", "b"])
        self.assertEqual(res["total_input_tokens"], 300)
        self.assertEqual(res["total_output_tokens"], 140)
        self.assertEqual(res["par_tokens"], 700)

    def test_rejects_foreign_not_passing_and_off_course_submissions(self):
        base = {"courses": [COURSE], "course_completions": []}
        use({**base, "submissions": [self._sub(id="a", user_id="other")]})
        with self.assertRaises(HTTPException):
            C.record_completion("u1", "c1", ["a"])
        use({**base, "submissions": [self._sub(id="a", passed=False)]})
        with self.assertRaises(HTTPException):
            C.record_completion("u1", "c1", ["a"])
        use({**base, "submissions": [self._sub(id="a", problem_id=999)]})
        with self.assertRaises(HTTPException):
            C.record_completion("u1", "c1", ["a"])
        use({**base, "submissions": []})
        with self.assertRaises(HTTPException):
            C.record_completion("u1", "c1", ["missing"])

    def test_requires_every_step(self):
        use({"courses": [COURSE], "course_completions": [], "submissions": [
            self._sub(id="a", problem_id=10),
        ]})
        with self.assertRaises(HTTPException):
            C.record_completion("u1", "c1", ["a"])  # step 20 missing

    def test_keeps_lower_total_on_rerun(self):
        store = {"courses": [COURSE], "submissions": [
            self._sub(id="a", problem_id=10, input_tokens=100, output_tokens=50),
            self._sub(id="b", problem_id=20, input_tokens=100, output_tokens=50),
        ], "course_completions": [
            {"user_id": "u1", "course_id": 1,
             "total_input_tokens": 120, "total_output_tokens": 60,
             "elapsed_seconds": 20, "completed_at": "2026-01-01T00:00:00Z"},
        ]}
        use(store)
        res = C.record_completion("u1", "c1", ["a", "b"])  # new total 300 > existing 180
        self.assertEqual(res["total_input_tokens"], 120)  # kept the better existing run
        self.assertEqual(len(store["course_completions"]), 1)  # no upsert appended


class TestCourseLeaderboard(unittest.TestCase):
    def test_orders_by_total_tokens_then_time(self):
        use({"courses": [COURSE], "course_completions": [
            {"user_id": "a", "total_input_tokens": 200, "total_output_tokens": 100,
             "elapsed_seconds": 10, "completed_at": "x", "course_id": 1, "profiles": {"username": "a"}},
            {"user_id": "b", "total_input_tokens": 100, "total_output_tokens": 100,
             "elapsed_seconds": 99, "completed_at": "x", "course_id": 1, "profiles": {"username": "b"}},
        ]})
        rows = C.course_leaderboard("c1")
        self.assertEqual([r["username"] for r in rows], ["b", "a"])


if __name__ == "__main__":
    unittest.main()
