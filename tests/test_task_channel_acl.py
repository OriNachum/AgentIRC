"""Tests for #task-* channel ACL enforcement (v8.18.7).

Verifies that:
- A worker can join its own #task-<suffix> channel.
- A foreign worker is refused from another worker's #task-<suffix> channel.
- #joint-* channels are always joinable by anyone.
- The boss of a worker can join that worker's #task-<suffix> channel.
- System channels (#team, #system) are unrestricted.
"""

from unittest.mock import patch

import pytest

from culture.agentirc.client import _task_channel_acl

# ---------------------------------------------------------------------------
# Unit tests for _task_channel_acl (no server needed)
# ---------------------------------------------------------------------------


def _mock_owner_map():
    """Simulated manifest: two workers owned by one boss."""
    return {
        "local-worker-a": "local-boss",
        "local-worker-b": "local-boss",
        "local-worker-c": "local-boss2",
    }


class TestTaskChannelAclUnit:
    """Unit tests for the ACL function itself."""

    def test_owner_allowed_own_task(self):
        """Worker can join its own task channel."""
        assert _task_channel_acl("local-worker-a", "#task-worker-a") is True

    def test_foreign_worker_refused(self):
        """Worker cannot join another worker's task channel."""
        with patch(
            "culture.agentirc.client._load_owner_map",
            return_value=_mock_owner_map(),
        ):
            assert _task_channel_acl("local-worker-b", "#task-worker-a") is False

    def test_boss_allowed_worker_task(self):
        """Boss can join its worker's task channel."""
        with patch(
            "culture.agentirc.client._load_owner_map",
            return_value=_mock_owner_map(),
        ):
            assert _task_channel_acl("local-boss", "#task-worker-a") is True

    def test_wrong_boss_refused(self):
        """A different boss cannot join another boss's worker's task channel."""
        with patch(
            "culture.agentirc.client._load_owner_map",
            return_value=_mock_owner_map(),
        ):
            assert _task_channel_acl("local-boss2", "#task-worker-a") is False

    def test_joint_channel_always_allowed(self):
        """#joint-* channels are open to everyone."""
        assert _task_channel_acl("local-worker-b", "#joint-fixes") is True
        assert _task_channel_acl("local-random", "#joint-coordination") is True

    def test_regular_channel_allowed(self):
        """Regular channels like #team are unrestricted."""
        assert _task_channel_acl("local-worker-a", "#team") is True
        assert _task_channel_acl("local-worker-a", "#system") is True
        assert _task_channel_acl("local-worker-a", "#general") is True

    def test_system_nick_always_allowed(self):
        """system-* nicks can join any task channel."""
        assert _task_channel_acl("system-local", "#task-worker-a") is True

    def test_no_manifest_owner_still_joins_own(self):
        """Owner can join own channel even without manifest."""
        with patch("culture.agentirc.client._load_owner_map", return_value={}):
            assert _task_channel_acl("local-worker-a", "#task-worker-a") is True

    def test_no_manifest_foreign_refused(self):
        """Foreign worker refused even without manifest (fail closed)."""
        with patch("culture.agentirc.client._load_owner_map", return_value={}):
            assert _task_channel_acl("local-worker-b", "#task-worker-a") is False


# ---------------------------------------------------------------------------
# Integration tests -- real IRCd, real TCP connections
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_owner_joins_own_task_channel(server, make_client):
    """Worker can JOIN its own #task-<suffix> channel."""
    client = await make_client(nick="testserv-worker-a", user="worker-a")
    await client.send("JOIN #task-worker-a")
    lines = await client.recv_all(timeout=1.0)
    joined = " ".join(lines)
    assert "JOIN" in joined
    assert "#task-worker-a" in joined
    assert "353" in joined  # RPL_NAMREPLY


@pytest.mark.asyncio
async def test_foreign_worker_refused_task_channel(server, make_client):
    """Foreign worker gets 474 (ERR_BANNEDFROMCHAN) on another's #task-*."""
    with patch(
        "culture.agentirc.client._load_owner_map",
        return_value=_mock_owner_map(),
    ):
        client = await make_client(nick="testserv-worker-b", user="worker-b")
        await client.send("JOIN #task-worker-a")
        response = await client.recv()
        assert "474" in response  # ERR_BANNEDFROMCHAN
        assert "#task-worker-a" in response


@pytest.mark.asyncio
async def test_joint_channel_always_joinable(server, make_client):
    """Any client can join a #joint-* channel."""
    client = await make_client(nick="testserv-worker-b", user="worker-b")
    await client.send("JOIN #joint-fixes")
    lines = await client.recv_all(timeout=1.0)
    joined = " ".join(lines)
    assert "JOIN" in joined
    assert "#joint-fixes" in joined


@pytest.mark.asyncio
async def test_boss_joins_worker_task_channel(server, make_client):
    """Boss can JOIN its worker's #task-* channel."""
    owner_map = {"testserv-worker-a": "testserv-boss"}
    with patch("culture.agentirc.client._load_owner_map", return_value=owner_map):
        client = await make_client(nick="testserv-boss", user="boss")
        await client.send("JOIN #task-worker-a")
        lines = await client.recv_all(timeout=1.0)
        joined = " ".join(lines)
        assert "JOIN" in joined
        assert "#task-worker-a" in joined
        assert "353" in joined  # RPL_NAMREPLY


@pytest.mark.asyncio
async def test_regular_channels_unrestricted(server, make_client):
    """#team and other normal channels remain open."""
    client = await make_client(nick="testserv-worker-a", user="worker-a")
    await client.send("JOIN #team")
    lines = await client.recv_all(timeout=1.0)
    joined = " ".join(lines)
    assert "JOIN" in joined
    assert "#team" in joined
