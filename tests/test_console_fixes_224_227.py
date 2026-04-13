"""Tests for console fixes covering issues #224, #225, #226, #227.

- #224  `/read` on exit overview + mouse copy-paste documentation
- #225  Newlines in IRC messages — CLI escape interpretation + observer split
- #226  Alt+Arrow word-jump (and Alt+Backspace) in chat input
- #227  Tab cycles channels (priority binding over Screen focus-cycling)
"""

from __future__ import annotations

import pytest

from culture.cli.channel import _interpret_escapes
from culture.console.app import ConsoleApp
from culture.console.widgets.chat import ChatInput
from culture.observer import IRCObserver

# ---------------------------------------------------------------------------
# #225 — CLI escape interpretation
# ---------------------------------------------------------------------------


class TestInterpretEscapes:
    """Convert shell-literal \\n / \\t sequences to real newlines / tabs."""

    def test_single_newline(self):
        assert _interpret_escapes(r"a\nb") == "a\nb"

    def test_multiple_newlines(self):
        assert _interpret_escapes(r"a\nb\nc") == "a\nb\nc"

    def test_tab(self):
        assert _interpret_escapes(r"col1\tcol2") == "col1\tcol2"

    def test_mixed(self):
        assert _interpret_escapes(r"line1\n\tindented") == "line1\n\tindented"

    def test_no_escapes(self):
        assert _interpret_escapes("plain text") == "plain text"

    def test_real_newlines_preserved(self):
        # Real newlines (e.g., from heredoc) passthrough unchanged.
        assert _interpret_escapes("a\nb") == "a\nb"

    def test_other_escapes_untouched(self):
        # Narrow scope: only \n and \t. Anything else (\f, \r, \x.., \\) is
        # passed through byte-for-byte.
        assert _interpret_escapes(r"a\fb") == r"a\fb"
        assert _interpret_escapes(r"a\rb") == r"a\rb"
        assert _interpret_escapes(r"a\\b") == r"a\\b"
        # And the literal \n we produce is a real newline, not a backslash-n.
        assert "\\n" not in _interpret_escapes(r"a\nb")


# ---------------------------------------------------------------------------
# #225 — observer multi-line PRIVMSG
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_observer_send_message_splits_newlines(server, make_client):
    """Issue #225: send_message emits one PRIVMSG per newline."""
    # Receiver joins and listens
    receiver = await make_client(nick="testserv-recv", user="recv")
    await receiver.send("JOIN #multiline")
    await receiver.recv_all(timeout=0.5)

    observer = IRCObserver(
        host="127.0.0.1",
        port=server.config.port,
        server_name=server.config.name,
    )
    await observer.send_message("#multiline", "line one\nline two\nline three")

    lines = await receiver.recv_all(timeout=1.0)
    joined = "\n".join(lines)

    # Each line must arrive as a separate PRIVMSG
    assert joined.count("PRIVMSG #multiline") >= 3
    assert "line one" in joined
    assert "line two" in joined
    assert "line three" in joined


@pytest.mark.asyncio
async def test_observer_send_message_drops_empty_lines(server, make_client):
    """Empty lines between real lines are dropped (IRC can't send empty PRIVMSG)."""
    receiver = await make_client(nick="testserv-recv2", user="recv2")
    await receiver.send("JOIN #drops")
    await receiver.recv_all(timeout=0.5)

    observer = IRCObserver(
        host="127.0.0.1",
        port=server.config.port,
        server_name=server.config.name,
    )
    await observer.send_message("#drops", "a\n\n\nb")

    lines = await receiver.recv_all(timeout=1.0)
    joined = "\n".join(lines)
    # Exactly two PRIVMSGs — the three blank segments are skipped
    assert joined.count("PRIVMSG #drops") == 2


# ---------------------------------------------------------------------------
# #226 — ChatInput bindings
# ---------------------------------------------------------------------------


class TestChatInputBindings:
    """ChatInput must expose Alt+Arrow word-jump and Alt+Backspace."""

    def _binding_map(self) -> dict[str, str]:
        return {b.key: b.action for b in ChatInput.BINDINGS}

    def test_alt_left_word_jump(self):
        assert self._binding_map().get("alt+left") == "cursor_left_word"

    def test_alt_right_word_jump(self):
        assert self._binding_map().get("alt+right") == "cursor_right_word"

    def test_alt_shift_selects_word(self):
        m = self._binding_map()
        assert m.get("alt+shift+left") == "cursor_left_word(True)"
        assert m.get("alt+shift+right") == "cursor_right_word(True)"

    def test_alt_backspace_deletes_word(self):
        assert self._binding_map().get("alt+backspace") == "delete_left_word"


# ---------------------------------------------------------------------------
# #227 — Tab cycles channels (priority binding)
# ---------------------------------------------------------------------------


class TestConsoleAppBindings:
    """App-level bindings for #227 and the Ctrl+H help follow-up."""

    def _bindings(self):
        return {b.key: b for b in ConsoleApp.BINDINGS}

    def test_tab_cycles_next_channel(self):
        b = self._bindings()["tab"]
        assert b.action == "next_channel"
        assert b.priority is True, "Tab must use priority to beat Screen focus-cycling"

    def test_shift_tab_cycles_prev_channel(self):
        b = self._bindings()["shift+tab"]
        assert b.action == "prev_channel"
        assert b.priority is True

    def test_help_is_bound_to_f1(self):
        # F1 is the primary help key — most terminals eat Ctrl+H as backspace.
        f1 = self._bindings()["f1"]
        assert f1.action == "show_help"

    def test_ctrl_h_remains_as_secondary_help(self):
        # Secondary binding still present for terminals with modifyOtherKeys.
        ctrl_h = self._bindings()["ctrl+h"]
        assert ctrl_h.action == "show_help"
