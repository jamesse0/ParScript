import pytest
from solution import Notification, User, Dispatcher


def test_delivers_in_channel_order():
    d = Dispatcher()
    u = User("A", ["email", "sms", "push"])
    assert d.send(u, Notification("hello team")) == [
        {"channel": "email", "message": "hello team"},
        {"channel": "sms", "message": "hello team"},
        {"channel": "push", "message": "🔔 hello team"},
    ]


def test_sms_truncates_at_20_chars():
    d = Dispatcher()
    u = User("A", ["sms"])
    assert d.send(u, Notification("x" * 50)) == [{"channel": "sms", "message": "x" * 20}]


def test_channel_order_is_per_user():
    d = Dispatcher()
    u = User("A", ["push", "email"])
    assert [r["channel"] for r in d.send(u, Notification("hi"))] == ["push", "email"]


def test_unknown_channel_raises_valueerror():
    d = Dispatcher()
    with pytest.raises(ValueError):
        d.send(User("A", ["carrier-pigeon"]), Notification("hi"))


def test_normal_priority_suppressed_under_dnd():
    d = Dispatcher()
    assert d.send(User("A", ["email"], dnd=True), Notification("hi")) == []


def test_urgent_priority_bypasses_dnd():
    d = Dispatcher()
    u = User("A", ["email"], dnd=True)
    assert d.send(u, Notification("alarm", priority="urgent")) == [
        {"channel": "email", "message": "alarm"}
    ]


def test_dispatcher_is_stateless_across_calls():
    d = Dispatcher()
    u = User("A", ["email"])
    first = d.send(u, Notification("one"))
    second = d.send(u, Notification("one"))
    assert first == second == [{"channel": "email", "message": "one"}]
