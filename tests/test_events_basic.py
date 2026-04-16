"""End-to-end: `emit_event` surfaces a tagged PRIVMSG from `system-<server>`."""

import asyncio
import base64
import json

import pytest

from culture.agentirc.skill import Event, EventType


@pytest.mark.asyncio
async def test_event_surfaces_as_tagged_privmsg(server, make_client):
    """A tag-capable client in #system receives a tagged PRIVMSG on emit_event."""
    c = await make_client("testserv-alice", "alice")
    await c.send("CAP REQ :message-tags")
    await c.recv_until("ACK")
    await c.send("JOIN #system")
    # Drain all JOIN responses including the join-event PRIVMSG that fires immediately.
    await c.recv_until("366")  # end of NAMES
    await asyncio.sleep(0.05)
    await c.recv_all(timeout=0.2)  # flush any queued join-event PRIVMSG

    # Simulate a server-originated event.
    ev = Event(
        type=EventType.AGENT_CONNECT,
        channel=None,
        nick="system-testserv",
        data={"nick": "testserv-bob"},
    )
    await server.emit_event(ev)

    line = await c.recv_until("agent.connect")
    assert line.startswith("@") or "@event=" in line
    assert "event=agent.connect" in line
    assert "event-data=" in line
    assert ":system-testserv!" in line
    assert " PRIVMSG #system :" in line
    assert "testserv-bob connected" in line


@pytest.mark.asyncio
async def test_channel_scoped_event_goes_to_channel(server, make_client):
    """A channel-scoped event is posted to its channel, not #system."""
    c = await make_client("testserv-alice", "alice")
    await c.send("CAP REQ :message-tags")
    await c.recv_until("ACK")
    await c.send("JOIN #general")
    # Drain all JOIN responses including the immediate join-event PRIVMSG.
    await c.recv_until("366")  # end of NAMES
    await asyncio.sleep(0.05)
    await c.recv_all(timeout=0.2)  # flush any queued join-event PRIVMSGs

    ev = Event(
        type=EventType.JOIN,
        channel="#general",
        nick="testserv-bob",
        data={"nick": "testserv-bob"},
    )
    await server.emit_event(ev)

    line = await c.recv_until("event=user.join")
    assert " PRIVMSG #general :" in line
    # EventType.JOIN.value is "user.join"
    assert "event=user.join" in line


@pytest.mark.asyncio
async def test_event_data_is_base64_json(server, make_client):
    c = await make_client("testserv-alice", "alice")
    await c.send("CAP REQ :message-tags")
    await c.recv_until("ACK")
    await c.send("JOIN #system")
    # Drain all JOIN responses including the immediate join-event PRIVMSG.
    await c.recv_until("366")  # end of NAMES
    await asyncio.sleep(0.05)
    await c.recv_all(timeout=0.2)  # flush any queued join-event PRIVMSGs

    ev = Event(
        type=EventType.AGENT_CONNECT,
        channel=None,
        nick="system-testserv",
        data={"nick": "testserv-bob"},
    )
    await server.emit_event(ev)

    line = await c.recv_until("agent.connect")
    # Extract the tag block from the received line(s)
    for raw_line in line.split("\r\n"):
        if "agent.connect" in raw_line:
            line = raw_line
            break
    if line.startswith("@"):
        tags = line.split(" ", 1)[0][1:]
    else:
        # find the @ block in the line
        at_idx = line.find("@")
        space_idx = line.find(" ", at_idx)
        tags = line[at_idx + 1 : space_idx]
    data_piece = [p for p in tags.split(";") if p.startswith("event-data=")][0]
    b64 = data_piece.split("=", 1)[1]
    decoded = json.loads(base64.b64decode(b64))
    assert decoded["nick"] == "testserv-bob"
