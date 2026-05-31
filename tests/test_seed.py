"""Tests for ``culture.clients._seed`` (v8.19.18) — channel seed persistence."""

import os
from unittest.mock import patch

import pytest

from culture.clients import _seed


@pytest.fixture
def isolated_culture_home(tmp_path):
    home = tmp_path / "culture-home"
    home.mkdir()
    with patch("culture.clients._perm_broker.culture_home", return_value=str(home)):
        yield home


def test_persist_and_load_roundtrip(isolated_culture_home):
    written = _seed.persist_seed("#task-alpha", "Build feature X with tests")
    assert written is True
    loaded = _seed.load_seed("#task-alpha")
    assert loaded is not None
    assert loaded["channel"] == "#task-alpha"
    assert loaded["text"] == "Build feature X with tests"
    # Timestamp comment is parseable from the header.
    assert loaded["ts"]


def test_persist_is_idempotent(isolated_culture_home):
    _seed.persist_seed("#task-beta", "original brief")
    second = _seed.persist_seed("#task-beta", "new brief")
    assert second is False, "second write without overwrite must be skipped"
    loaded = _seed.load_seed("#task-beta")
    assert loaded["text"] == "original brief"


def test_persist_overwrite_replaces(isolated_culture_home):
    _seed.persist_seed("#task-gamma", "original")
    _seed.persist_seed("#task-gamma", "updated", overwrite=True)
    loaded = _seed.load_seed("#task-gamma")
    assert loaded["text"] == "updated"


def test_persist_empty_text_skips(isolated_culture_home):
    assert _seed.persist_seed("#task-empty", "") is False
    assert _seed.persist_seed("#task-empty", "   \n\n   ") is False
    assert _seed.load_seed("#task-empty") is None


def test_load_missing_returns_none(isolated_culture_home):
    assert _seed.load_seed("#never-seeded") is None


def test_clear_removes(isolated_culture_home):
    _seed.persist_seed("#task-clr", "to remove")
    assert _seed.clear_seed("#task-clr") is True
    assert _seed.load_seed("#task-clr") is None
    assert _seed.clear_seed("#task-clr") is False, "second clear is no-op"


def test_persist_unsafe_channel_name_skips(isolated_culture_home):
    # Path-traversal must be rejected by seed_path_for; persist_seed
    # catches the ValueError and returns False.
    assert _seed.persist_seed("#../escape", "no") is False
    assert _seed.persist_seed("#with spaces", "no") is False


def test_multiline_seed_preserves_lines(isolated_culture_home):
    body = "Title line\n\nBody paragraph with details.\nAnd another line."
    _seed.persist_seed("#task-multi", body)
    loaded = _seed.load_seed("#task-multi")
    assert loaded["text"] == body


def test_file_lives_under_culture_home(isolated_culture_home):
    _seed.persist_seed("#task-onpath", "ok")
    seed_path = isolated_culture_home / "seeds" / "task-onpath.md"
    assert seed_path.exists()
    assert "ok" in seed_path.read_text(encoding="utf-8")
