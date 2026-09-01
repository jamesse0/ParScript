import pytest
from solution import Calendar


# --- carried from steps 1-2 ---
def test_overlap_and_cancel_still_work():
    c = Calendar()
    c.book("A", 9, 10)
    with pytest.raises(ValueError):
        c.book("A", 9, 10)
    c.cancel("A", 9)
    assert c.is_free("A", 9, 10)


def test_bookings_still_sorted():
    c = Calendar()
    c.book("A", 14, 15)
    c.book("A", 9, 10)
    assert c.bookings("A") == [(9, 10), (14, 15)]


# --- new in step 3 ---
def test_recurring_books_every_occurrence():
    c = Calendar()
    c.book_recurring("A", 9, 10, count=3, period=24)
    assert c.bookings("A") == [(9, 10), (33, 34), (57, 58)]


def test_recurring_is_all_or_nothing():
    c = Calendar()
    c.book("A", 33, 34)  # blocks the 2nd occurrence
    with pytest.raises(ValueError):
        c.book_recurring("A", 9, 10, count=3, period=24)
    assert c.bookings("A") == [(33, 34)]  # nothing else was booked


def test_recurring_then_cancel_one_occurrence():
    c = Calendar()
    c.book_recurring("A", 9, 10, count=2, period=24)
    c.cancel("A", 33)
    assert c.bookings("A") == [(9, 10)]


def test_recurring_count_one():
    c = Calendar()
    c.book_recurring("A", 9, 10, count=1, period=24)
    assert c.bookings("A") == [(9, 10)]
