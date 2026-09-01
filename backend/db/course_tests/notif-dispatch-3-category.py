import pytest
from solution import Notification, User, Dispatcher


# --- carried from steps 1-2 (unchanged) ---
def test_plain_notification_formats_as_before():
    d = Dispatcher()
    u = User("A", ["email", "sms", "push", "slack"])
    assert d.send(u, Notification("hello team")) == [
        {"channel": "email", "message": "hello team"},
        {"channel": "sms", "message": "hello team"},
        {"channel": "push", "message": "🔔 hello team"},
        {"channel": "slack", "message": "*hello team*"},
    ]


def test_dnd_and_priority_unchanged():
    d = Dispatcher()
    u = User("A", ["email"], dnd=True)
    assert d.send(u, Notification("hi")) == []
    assert d.send(u, Notification("hi", priority="urgent")) == [
        {"channel": "email", "message": "hi"}
    ]


def test_unknown_channel_still_raises():
    d = Dispatcher()
    with pytest.raises(ValueError):
        d.send(User("A", ["fax"]), Notification("hi"))


# --- new in step 3 ---
def test_category_prefixes_each_channel_in_its_own_style():
    d = Dispatcher()
    u = User("A", ["email", "push", "slack"])
    assert d.send(u, Notification("shipped", category="Deploys")) == [
        {"channel": "email", "message": "[Deploys] shipped"},
        {"channel": "push", "message": "🔔 [Deploys] shipped"},
        {"channel": "slack", "message": "*[Deploys]* shipped"},
    ]


def test_sms_prefixes_then_truncates_to_20():
    d = Dispatcher()
    u = User("A", ["sms"])
    # "Alerts: " (8 chars) + the message, whole thing capped at 20
    assert d.send(u, Notification("abcdefghijklmnop", category="Alerts")) == [
        {"channel": "sms", "message": "Alerts: abcdefghijkl"}
    ]


def test_no_category_is_unchanged():
    d = Dispatcher()
    u = User("A", ["email", "slack"])
    assert d.send(u, Notification("hi")) == [
        {"channel": "email", "message": "hi"},
        {"channel": "slack", "message": "*hi*"},
    ]


def test_category_respects_dnd():
    d = Dispatcher()
    assert d.send(User("A", ["email"], dnd=True), Notification("hi", category="X")) == []


def test_category_with_urgent_priority():
    d = Dispatcher()
    u = User("A", ["push"], dnd=True)
    assert d.send(u, Notification("down", category="Ops", priority="urgent")) == [
        {"channel": "push", "message": "🔔 [Ops] down"}
    ]
