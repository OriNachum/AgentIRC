"""Tests for overview collector against a real IRC server."""

import asyncio
from unittest.mock import patch

import pytest

from culture.constants import SYSTEM_CHANNEL, SYSTEM_USER_PREFIX
from culture.overview.collector import _collect_bots, collect_mesh_state
from culture.overview.model import MeshState


@pytest.mark.asyncio
async def test_collect_empty_server(server):
    """Collecting from an empty server returns no user rooms or agents.

    #system is always present (auto-created at IRCd startup) but is a
    server-internal channel — it is filtered out of the user-visible
    room/agent lists here.
    """
    mesh = await collect_mesh_state(
        host="127.0.0.1",
        port=server.config.port,
        server_name=server.config.name,
        message_limit=4,
    )
    assert isinstance(mesh, MeshState)
    assert mesh.server_name == server.config.name
    user_rooms = [r for r in mesh.rooms if r.name != SYSTEM_CHANNEL]
    user_agents = [a for a in mesh.agents if not a.nick.startswith(SYSTEM_USER_PREFIX)]
    assert user_rooms == []
    assert user_agents == []


@pytest.mark.asyncio
async def test_collect_with_agent_in_channel(server, make_client):
    """Collecting sees agents and channels (excluding the server-internal #system room)."""
    client = await make_client(nick="testserv-agent1", user="agent1")
    await client.send("JOIN #testing")
    await client.recv_all(timeout=0.5)

    mesh = await collect_mesh_state(
        host="127.0.0.1",
        port=server.config.port,
        server_name=server.config.name,
        message_limit=4,
    )
    user_rooms = [r for r in mesh.rooms if r.name != SYSTEM_CHANNEL]
    assert len(user_rooms) == 1
    testing_room = user_rooms[0]
    assert testing_room.name == "#testing"
    assert len(testing_room.members) >= 1
    found = any(a.nick == "testserv-agent1" for a in testing_room.members)
    assert found


@pytest.mark.asyncio
async def test_collect_sees_topic(server, make_client):
    """Collecting includes channel topics."""
    client = await make_client(nick="testserv-agent1", user="agent1")
    await client.send("JOIN #testing")
    await client.recv_all(timeout=0.5)
    await client.send("TOPIC #testing :Hello world topic")
    await client.recv_all(timeout=0.5)

    mesh = await collect_mesh_state(
        host="127.0.0.1",
        port=server.config.port,
        server_name=server.config.name,
        message_limit=4,
    )
    testing_room = next(r for r in mesh.rooms if r.name == "#testing")
    assert testing_room.topic == "Hello world topic"


@pytest.mark.asyncio
async def test_collect_sees_messages(server, make_client):
    """Collecting includes recent messages via HISTORY."""
    client = await make_client(nick="testserv-agent1", user="agent1")
    await client.send("JOIN #testing")
    await client.recv_all(timeout=0.5)
    await client.send("PRIVMSG #testing :test message one")
    await client.send("PRIVMSG #testing :test message two")
    await asyncio.sleep(0.3)

    mesh = await collect_mesh_state(
        host="127.0.0.1",
        port=server.config.port,
        server_name=server.config.name,
        message_limit=4,
    )
    testing_room = next(r for r in mesh.rooms if r.name == "#testing")
    assert len(testing_room.messages) == 2
    assert testing_room.messages[0].text == "test message one"
    assert testing_room.messages[1].text == "test message two"


@pytest.mark.asyncio
async def test_collect_multiple_rooms(server, make_client):
    """Collecting sees all rooms."""
    c1 = await make_client(nick="testserv-a", user="a")
    c2 = await make_client(nick="testserv-b", user="b")
    await c1.send("JOIN #room1")
    await c2.send("JOIN #room2")
    await c1.recv_all(timeout=0.5)
    await c2.recv_all(timeout=0.5)

    mesh = await collect_mesh_state(
        host="127.0.0.1",
        port=server.config.port,
        server_name=server.config.name,
        message_limit=4,
    )
    room_names = sorted(r.name for r in mesh.rooms)
    assert "#room1" in room_names
    assert "#room2" in room_names


def test_collect_bots_passes_archived_flag(tmp_path):
    """Issue #184: _collect_bots should populate BotInfo.archived from config."""
    # Create a bot directory with an archived bot config (nested YAML format)
    bot_dir = tmp_path / "test-bot"
    bot_dir.mkdir()
    (bot_dir / "bot.yaml").write_text(
        "bot:\n"
        "  name: test-bot\n"
        "  owner: spark\n"
        "  archived: true\n"
        "  archived_at: '2026-01-01'\n"
        "  archived_reason: testing\n"
        "trigger:\n"
        "  type: webhook\n"
        "output:\n"
        "  channels:\n"
        "    - '#general'\n"
    )

    # Create a non-archived bot
    active_dir = tmp_path / "active-bot"
    active_dir.mkdir()
    (active_dir / "bot.yaml").write_text(
        "bot:\n"
        "  name: active-bot\n"
        "  owner: spark\n"
        "trigger:\n"
        "  type: mention\n"
        "output:\n"
        "  channels:\n"
        "    - '#general'\n"
    )

    with patch("culture.bots.config.BOTS_DIR", tmp_path):
        bots = _collect_bots()

    assert len(bots) == 2
    archived_bot = next(b for b in bots if b.name == "test-bot")
    active_bot = next(b for b in bots if b.name == "active-bot")
    assert archived_bot.archived is True
    assert active_bot.archived is False
