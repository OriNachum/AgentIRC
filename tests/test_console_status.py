"""Tests for console status polling module."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from culture.console.status import discover_agent_sockets, query_all_agents


def test_discover_no_sockets(tmp_path):
    """discover_agent_sockets returns empty list when no sockets exist."""
    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(tmp_path)}):
        result = discover_agent_sockets()
    assert result == []


def test_discover_finds_sockets(tmp_path):
    """discover_agent_sockets finds culture-*.sock files."""
    sock1 = tmp_path / "culture-spark-claude.sock"
    sock1.touch()
    sock2 = tmp_path / "culture-spark-daria.sock"
    sock2.touch()
    # Non-matching file should be ignored
    (tmp_path / "other.sock").touch()

    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(tmp_path)}):
        result = discover_agent_sockets()

    nicks = [nick for nick, _ in result]
    assert sorted(nicks) == ["spark-claude", "spark-daria"]


@pytest.mark.asyncio
async def test_query_all_agents_no_sockets(tmp_path):
    """query_all_agents returns empty dict when no sockets exist."""
    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(tmp_path)}):
        result = await query_all_agents()
    assert result == {}
