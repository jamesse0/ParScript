import pytest
from solution import Calendar


def test_book_and_is_free():
    c = Calendar()
    assert c.is_free("A", 9, 10)
    c.book("A", 9, 10)
    assert not c.is_free("A", 9, 10)


def test_touching_intervals_are_allowed():
    c = Calendar()
    c.book("A", 9, 10)
    c.book("A", 10, 11)
    assert not c.is_free("A", 9, 11)


def test_overlap_is_rejected():
    c = Calendar()
    c.book("A", 9, 11)
    with pytest.raises(ValueError):
        c.book("A", 10, 12)


def test_rooms_are_independent():
    c = Calendar()
    c.book("A", 9, 10)
    assert c.is_free("B", 9, 10)


def test_partial_overlap_is_not_free():
    c = Calendar()
    c.book("A", 9, 12)
    assert not c.is_free("A", 11, 13)
    assert c.is_free("A", 12, 13)
