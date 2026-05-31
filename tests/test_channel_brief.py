"""Tests for ``culture.clients._channel_brief`` (v8.19.24) — living
per-channel onboarding doc.

User flagged that new mesh workers join with no onboarding context —
they get the IRC HISTORY (last N messages) and that's it. The v8.19.18
seed is *write-once initial*; this module is the *living* sibling.
Every brief / note appends a dated section so a new joiner can read
the running team state.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from culture.clients import _channel_brief


@pytest.fixture
def isolated_home(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    with (
        patch("culture.clients._perm_broker.culture_home", return_value=str(home)),
        patch("culture.clients._channel_brief.culture_home", return_value=str(home)),
    ):
        yield home


# --- persist + load roundtrip ----------------------------------------------


def test_first_persist_creates_file_with_header(isolated_home):
    ok = _channel_brief.persist_section("#task-alpha", "kickoff", "Build feature X.")
    assert ok is True
    text = _channel_brief.load_brief("#task-alpha")
    assert "# Channel brief — #task-alpha" in text
    assert "kickoff" in text
    assert "Build feature X." in text


def test_subsequent_persists_append(isolated_home):
    _channel_brief.persist_section("#task-alpha", "kickoff", "First brief.")
    _channel_brief.persist_section("#task-alpha", "decision", "We chose Postgres.")
    _channel_brief.persist_section("#task-alpha", "done", "Migration applied.")
    text = _channel_brief.load_brief("#task-alpha")
    assert "First brief." in text
    assert "We chose Postgres." in text
    assert "Migration applied." in text
    # All three section headers present.
    assert text.count("## ") == 3


def test_empty_body_skipped(isolated_home):
    assert _channel_brief.persist_section("#task-empty", "x", "") is False
    assert _channel_brief.persist_section("#task-empty", "x", "   \n\n  ") is False
    assert _channel_brief.load_brief("#task-empty") == ""


def test_unsafe_channel_name_skipped(isolated_home):
    assert _channel_brief.persist_section("#../escape", "x", "no") is False
    assert _channel_brief.persist_section("#with spaces", "x", "no") is False


def test_has_brief_returns_false_for_unknown(isolated_home):
    assert _channel_brief.has_brief("#never-touched") is False


def test_has_brief_returns_true_after_persist(isolated_home):
    _channel_brief.persist_section("#task-x", "k", "v")
    assert _channel_brief.has_brief("#task-x") is True


def test_clear_removes(isolated_home):
    _channel_brief.persist_section("#task-clr", "k", "v")
    assert _channel_brief.clear_brief("#task-clr") is True
    assert _channel_brief.has_brief("#task-clr") is False
    assert _channel_brief.clear_brief("#task-clr") is False  # idempotent


# --- Idempotence -----------------------------------------------------------


def test_identical_body_within_minute_is_idempotent(isolated_home):
    """Repeated identical writes within the same minute window should
    skip — defends against duplicate brief fires."""
    a = _channel_brief.persist_section("#task-dup", "brief", "Identical body.")
    b = _channel_brief.persist_section("#task-dup", "brief", "Identical body.")
    assert a is True
    # Idempotence catches the SAME content + header in close window.
    assert b is False, "second identical write within the minute must be skipped"


def test_different_body_appends_even_within_minute(isolated_home):
    a = _channel_brief.persist_section("#task-vary", "brief", "First.")
    b = _channel_brief.persist_section("#task-vary", "brief", "Second.")
    assert a is True
    assert b is True
    text = _channel_brief.load_brief("#task-vary")
    assert "First." in text and "Second." in text


# --- Read cap --------------------------------------------------------------


def test_load_brief_truncates_above_cap(isolated_home, monkeypatch):
    """A multi-megabyte brief must read as the TAIL (recent state),
    capped at READ_CAP_BYTES, so a runaway file can't break a worker."""
    # Set the cap tiny so this test stays fast.
    monkeypatch.setattr(_channel_brief, "READ_CAP_BYTES", 200)
    # Write a long brief.
    path = _channel_brief.brief_path_for("#task-long")
    import os

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        # 5000 bytes of "OLDOLDOLD" then RECENT marker.
        fh.write("OLD\n" * 1250)
        fh.write("RECENT_MARKER\n")
    text = _channel_brief.load_brief("#task-long")
    assert len(text) < 500, f"expected truncated read, got {len(text)} bytes"
    assert "RECENT_MARKER" in text
    assert "older history truncated" in text


# --- system_prompt_extension -----------------------------------------------


def test_system_prompt_extension_wraps_with_framing(isolated_home):
    _channel_brief.persist_section("#task-alpha", "kickoff", "Build feature X.")
    ext = _channel_brief.system_prompt_extension("#task-alpha")
    assert "joining channel #task-alpha" in ext.lower()
    assert "Build feature X." in ext
    assert "End of channel brief" in ext


def test_system_prompt_extension_empty_when_no_brief(isolated_home):
    assert _channel_brief.system_prompt_extension("#nope") == ""


# --- File location safety --------------------------------------------------


def test_file_lives_under_culture_home(isolated_home):
    _channel_brief.persist_section("#task-x", "k", "v")
    expected = isolated_home / "briefs" / "task-x.md"
    assert expected.exists()


def test_brief_path_rejects_traversal(isolated_home):
    with pytest.raises(ValueError):
        _channel_brief.brief_path_for("#../etc/passwd")
    with pytest.raises(ValueError):
        _channel_brief.brief_path_for("#name with space")
