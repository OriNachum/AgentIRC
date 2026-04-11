"""Tests for console status polling module."""

from __future__ import annotations

import os
import socket
from unittest.mock import patch

import pytest

from culture.console.status import discover_agent_sockets, query_all_agents


def _make_unix_socket(path):
    """Create a Unix domain socket at *path* and return it (caller closes)."""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(path))
    return sock


def test_discover_no_sockets(tmp_path):
    """discover_agent_sockets returns empty list when no sockets exist."""
    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(tmp_path)}):
        result = discover_agent_sockets()
    assert result == []


def test_discover_finds_sockets(tmp_path):
    """discover_agent_sockets finds culture-*.sock Unix sockets."""
    socks = []
    for name in ("culture-spark-claude.sock", "culture-spark-daria.sock"):
        socks.append(_make_unix_socket(tmp_path / name))
    # Regular file with matching name should be ignored (not a socket)
    (tmp_path / "culture-spark-fake.sock").touch()
    # Non-matching socket-like file should also be ignored
    (tmp_path / "other.sock").touch()

    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(tmp_path)}):
        result = discover_agent_sockets()

    nicks = [nick for nick, _ in result]
    assert sorted(nicks) == ["spark-claude", "spark-daria"]

    for s in socks:
        s.close()


@pytest.mark.asyncio
async def test_query_all_agents_no_sockets(tmp_path):
    """query_all_agents returns empty dict when no sockets exist."""
    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(tmp_path)}):
        result = await query_all_agents()
    assert result == {}
