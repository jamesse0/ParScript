import time
import pytest
from solution import Cache


def test_basic_get_put():
    c = Cache(capacity=2)
    c.put("a", 1)
    assert c.get("a") == 1


def test_get_missing_key_returns_none():
    c = Cache(capacity=2)
    assert c.get("nope") is None


def test_lru_eviction_order():
    c = Cache(capacity=2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")  # "a" is now more recently used than "b"
    c.put("c", 3)  # should evict "b", not "a"
    assert c.get("b") is None
    assert c.get("a") == 1
    assert c.get("c") == 3


def test_ttl_expiry():
    c = Cache(capacity=2)
    c.put("a", 1, ttl_seconds=0.3)
    time.sleep(0.4)
    assert c.get("a") is None


def test_no_ttl_never_expires():
    c = Cache(capacity=2)
    c.put("a", 1)
    time.sleep(0.3)
    assert c.get("a") == 1


def test_expired_get_does_not_count_as_use():
    c = Cache(capacity=2)
    c.put("a", 1, ttl_seconds=0.2)
    c.put("b", 2)
    time.sleep(0.3)  # "a" now expired
    c.get("a")  # should NOT refresh "a"'s LRU position
    c.put("c", 3)  # capacity exceeded -> evict LRU; "a" expired anyway
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_put_existing_key_keeps_lru_position():
    c = Cache(capacity=2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 99)  # overwrite, but does NOT refresh LRU position
    c.put("c", 3)  # should evict "a" (still least-recently-used)
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_put_existing_key_updates_value_and_ttl():
    c = Cache(capacity=2)
    c.put("a", 1, ttl_seconds=0.2)
    time.sleep(0.1)
    c.put("a", 2, ttl_seconds=0.5)  # new ttl resets expiry
    time.sleep(0.3)  # 0.3s after the second put -> still live
    assert c.get("a") == 2


def test_size_excludes_expired_items():
    c = Cache(capacity=3)
    c.put("a", 1, ttl_seconds=0.2)
    c.put("b", 2)
    time.sleep(0.3)
    assert c.size() == 1


def test_prefers_evicting_expired_over_live():
    c = Cache(capacity=2)
    c.put("a", 1, ttl_seconds=0.2)
    c.put("b", 2)
    time.sleep(0.3)  # "a" expired, "b" still live
    c.put("c", 3)  # should evict expired "a", not live "b"
    assert c.get("b") == 2
    assert c.get("c") == 3
