import pytest
from solution import Calendar


# --- carried from step 1 (must still pass) ---
def test_still_rejects_overlap():
    c = Calendar()
    c.book("A", 9, 11)
    with pytest.raises(ValueError):
        c.book("A", 10, 12)


def test_touching_still_allowed():
    c = Calendar()
    c.book("A", 9, 10)
    c.book("A", 10, 11)
    assert not c.is_free("A", 9, 11)


# --- new in step 2 ---
def test_cancel_frees_the_slot():
    c = Calendar()
    c.book("A", 9, 10)
    c.cancel("A", 9)
    assert c.is_free("A", 9, 10)


def test_cancel_missing_raises_keyerror():
    c = Calendar()
    c.book("A", 9, 10)
    with pytest.raises(KeyError):
        c.cancel("A", 15)


def test_bookings_sorted_by_start():
    c = Calendar()
    c.book("A", 14, 15)
    c.book("A", 9, 10)
    c.book("A", 11, 12)
    assert c.bookings("A") == [(9, 10), (11, 12), (14, 15)]


def test_bookings_of_unknown_room_is_empty():
    c = Calendar()
    assert c.bookings("Z") == []
