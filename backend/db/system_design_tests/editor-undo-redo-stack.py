import pytest
from solution import Command, Editor


class AppendText(Command):
    def __init__(self, text):
        self.text = text

    def do(self, editor):
        editor.text += self.text

    def undo(self, editor):
        editor.text = editor.text[: -len(self.text)]


class UppercaseLast(Command):
    """Uppercases the last n characters of editor.text.
    Stateful command: captures what it overwrote so undo can restore it."""

    def __init__(self, n):
        self.n = n
        self._prev = None

    def do(self, editor):
        self._prev = editor.text[-self.n :]
        editor.text = editor.text[: -self.n] + editor.text[-self.n :].upper()

    def undo(self, editor):
        editor.text = editor.text[: -self.n] + self._prev


def test_execute_applies_command():
    e = Editor()
    e.execute(AppendText("hello"))
    assert e.text == "hello"


def test_undo_reverts_last_command():
    e = Editor()
    e.execute(AppendText("hello"))
    result = e.undo()
    assert result is True
    assert e.text == ""


def test_undo_on_empty_history_is_safe_noop():
    e = Editor()
    result = e.undo()
    assert result is False
    assert e.text == ""


def test_redo_reapplies_undone_command():
    e = Editor()
    e.execute(AppendText("hello"))
    e.undo()
    result = e.redo()
    assert result is True
    assert e.text == "hello"


def test_redo_on_empty_history_is_safe_noop():
    e = Editor()
    e.execute(AppendText("hello"))
    result = e.redo()
    assert result is False
    assert e.text == "hello"


def test_execute_after_undo_clears_redo_stack():
    e = Editor()
    e.execute(AppendText("a"))
    e.execute(AppendText("b"))
    e.undo()  # back to "a", "b" is now redoable
    e.execute(AppendText("c"))  # new work -> redo history must be discarded
    assert e.text == "ac"
    result = e.redo()
    assert result is False  # nothing to redo; "b" must not resurrect
    assert e.text == "ac"


def test_multiple_undo_then_multiple_redo_restores_each_intermediate_state():
    e = Editor()
    e.execute(AppendText("a"))
    e.execute(AppendText("b"))
    e.execute(AppendText("c"))
    assert e.text == "abc"

    e.undo()
    assert e.text == "ab"
    e.undo()
    assert e.text == "a"
    e.undo()
    assert e.text == ""
    assert e.undo() is False  # exhausted

    e.redo()
    assert e.text == "a"
    e.redo()
    assert e.text == "ab"
    e.redo()
    assert e.text == "abc"
    assert e.redo() is False  # exhausted


def test_undo_calls_command_undo_not_do():
    # If undo mistakenly called do() again instead of undo(), this would
    # append "x" a second time instead of removing it.
    e = Editor()
    e.execute(AppendText("x"))
    e.undo()
    assert e.text == ""


def test_stateful_command_undo_uses_captured_state():
    e = Editor()
    e.execute(AppendText("hello"))
    e.execute(UppercaseLast(3))
    assert e.text == "heLLO"
    e.undo()
    assert e.text == "hello"
    e.undo()
    assert e.text == ""


def test_interleaved_commands_undo_redo_consistency():
    e = Editor()
    e.execute(AppendText("ab"))
    e.execute(UppercaseLast(1))
    e.execute(AppendText("cd"))
    assert e.text == "aBcd"

    e.undo()
    assert e.text == "aB"
    e.undo()
    assert e.text == "ab"

    e.redo()
    assert e.text == "aB"
    e.redo()
    assert e.text == "aBcd"