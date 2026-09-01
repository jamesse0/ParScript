import pytest
from solution import Notification, User, Dispatcher


# --- carried from steps 1-3 ---
def test_immediate_delivery_unchanged_for_normal_users():
    d = Dispatcher()
    u = User("A", ["email", "push"])
    assert d.send(u, Notification("hi")) == [
        {"channel": "email", "message": "hi"},
        {"channel": "push", "message": "🔔 hi"},
    ]


def test_category_still_prefixes():
    d = Dispatcher()
    u = User("A", ["slack"])
    assert d.send(u, Notification("shipped", category="Deploys")) == [
        {"channel": "slack", "message": "*[Deploys]* shipped"}
    ]


# --- new in step 4 ---
def test_digest_queues_until_batch_size():
    d = Dispatcher()
    u = User("A", ["email"], digest_size=3)
    assert d.send(u, Notification("one")) == []
    assert d.send(u, Notification("two")) == []
    assert d.send(u, Notification("three")) == [
        {"channel": "email", "message": "one\ntwo\nthree"}
    ]


def test_digest_combines_one_message_per_channel():
    d = Dispatcher()
    u = User("A", ["push", "slack"], digest_size=2)
    d.send(u, Notification("a"))
    assert d.send(u, Notification("b")) == [
        {"channel": "push", "message": "🔔 a\nb"},
        {"channel": "slack", "message": "*a\nb*"},
    ]


def test_explicit_flush_delivers_partial_batch():
    d = Dispatcher()
    u = User("A", ["email"], digest_size=5)
    d.send(u, Notification("one"))
    d.send(u, Notification("two"))
    assert d.flush(u) == [{"channel": "email", "message": "one\ntwo"}]


def test_flush_clears_the_queue():
    d = Dispatcher()
    u = User("A", ["email"], digest_size=5)
    d.send(u, Notification("one"))
    d.flush(u)
    assert d.flush(u) == []


def test_batch_resets_after_auto_flush():
    d = Dispatcher()
    u = User("A", ["email"], digest_size=2)
    d.send(u, Notification("one"))
    d.send(u, Notification("two"))  # auto-flush here
    assert d.send(u, Notification("three")) == []  # a fresh batch has started


def test_non_digest_user_unaffected_by_flush():
    d = Dispatcher()
    u = User("A", ["email"])
    d.send(u, Notification("hi"))
    assert d.flush(u) == []
