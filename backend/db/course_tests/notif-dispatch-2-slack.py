import pytest
from solution import Notification, User, Dispatcher


# --- carried from step 1 ---
def test_core_channels_unchanged():
    d = Dispatcher()
    u = User("A", ["email", "sms", "push"])
    assert d.send(u, Notification("hello team")) == [
        {"channel": "email", "message": "hello team"},
        {"channel": "sms", "message": "hello team"},
        {"channel": "push", "message": "🔔 hello team"},
    ]


def test_unknown_channel_still_raises():
    d = Dispatcher()
    with pytest.raises(ValueError):
        d.send(User("A", ["fax"]), Notification("hi"))


def test_dnd_and_priority_unchanged():
    d = Dispatcher()
    u = User("A", ["email"], dnd=True)
    assert d.send(u, Notification("hi")) == []
    assert d.send(u, Notification("hi", priority="urgent")) == [
        {"channel": "email", "message": "hi"}
    ]


# --- new in step 2 ---
def test_slack_channel_has_its_own_format():
    d = Dispatcher()
    u = User("A", ["slack"])
    assert d.send(u, Notification("deploy done")) == [
        {"channel": "slack", "message": "*deploy done*"}
    ]


def test_slack_slots_into_channel_order():
    d = Dispatcher()
    u = User("A", ["email", "slack", "push"])
    assert d.send(u, Notification("ping")) == [
        {"channel": "email", "message": "ping"},
        {"channel": "slack", "message": "*ping*"},
        {"channel": "push", "message": "🔔 ping"},
    ]


def test_slack_respects_dnd():
    d = Dispatcher()
    assert d.send(User("A", ["slack"], dnd=True), Notification("quiet")) == []
