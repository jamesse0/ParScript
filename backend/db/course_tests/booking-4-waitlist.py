import pytest
from solution import Calendar


# --- carried from steps 1-3 ---
def test_core_booking_still_works():
    c = Calendar()
    c.book("A", 9, 10)
    with pytest.raises(ValueError):
        c.book("A", 9, 10)
    assert c.bookings("A") == [(9, 10)]


def test_recurring_still_all_or_nothing():
    c = Calendar()
    c.book("A", 33, 34)
    with pytest.raises(ValueError):
        c.book_recurring("A", 9, 10, count=3, period=24)
    assert c.bookings("A") == [(33, 34)]


# --- new in step 4 ---
def test_waitlist_does_not_book_while_busy():
    c = Calendar()
    c.book("A", 9, 10)
    assert c.waitlist("A", 9, 10) is None
    assert c.bookings("A") == [(9, 10)]


def test_cancel_promotes_a_waitlisted_request():
    c = Calendar()
    c.book("A", 9, 10)
    c.waitlist("A", 9, 10)
    promoted = c.cancel("A", 9)
    assert promoted == (9, 10)
    assert not c.is_free("A", 9, 10)


def test_cancel_promotes_earliest_start_that_fits():
    c = Calendar()
    c.book("A", 9, 12)
    c.waitlist("A", 10, 11)
    c.waitlist("A", 9, 10)
    assert c.cancel("A", 9) == (9, 10)


def test_cancel_with_empty_waitlist_returns_none():
    c = Calendar()
    c.book("A", 9, 10)
    assert c.cancel("A", 9) is None


def test_waitlisted_request_that_still_does_not_fit_is_skipped():
    c = Calendar()
    c.book("A", 9, 10)
    c.book("A", 10, 11)
    c.waitlist("A", 9, 11)
    assert c.cancel("A", 9) is None
    assert c.is_free("A", 9, 10)
