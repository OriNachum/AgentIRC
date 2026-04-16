"""Events appear in HISTORY RECENT replays."""

import asyncio

import pytest

from culture.agentirc.skill import Event, EventType


@pytest.mark.asyncio
async def test_event_appears_in_history(server, make_client):
    """A global event (agent.connect) appears in #system HISTORY RECENT."""
    alice = await make_client("testserv-alice", "alice")
    await alice.send("CAP REQ :message-tags")
    await alice.recv_until("CAP")

    # Emit an event before the client joins #system.
    await server.emit_event(
        Event(
            type=EventType.AGENT_CONNECT,
            channel=None,
            nick="system-testserv",
            data={"nick": "testserv-claude"},
        )
    )

    await alice.send("JOIN #system")
    await alice.recv_until("JOIN")
    # Flush any surfaced PRIVMSGs from the join
    await asyncio.sleep(0.05)
    await alice.recv_all(timeout=0.2)

    await alice.send("HISTORY RECENT #system 50")
    history = await alice.recv_until("HISTORYEND")
    assert "testserv-claude connected" in history


@pytest.mark.asyncio
async def test_channel_event_in_channel_history(server, make_client):
    """A channel-scoped event (room.create) appears in that channel's history."""
    alice = await make_client("testserv-alice", "alice")
    await alice.send("CAP REQ :message-tags")
    await alice.recv_until("CAP")
    await alice.send("JOIN #room")
    await alice.recv_until("JOIN")
    # Flush join-related messages
    await asyncio.sleep(0.05)
    await alice.recv_all(timeout=0.2)

    await server.emit_event(
        Event(
            type=EventType.ROOM_CREATE,
            channel="#room",
            nick="testserv-bob",
            data={"nick": "testserv-bob", "room": "#room"},
        )
    )

    # Wait for event to be processed
    await asyncio.sleep(0.05)

    await alice.send("HISTORY RECENT #room 50")
    history = await alice.recv_until("HISTORYEND")
    assert "created room #room" in history
