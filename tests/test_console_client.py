"""Tests for ConsoleIRCClient.

Uses a real IRCd instance (no mocks) following the same patterns
as test_irc_transport.py and test_history.py.
"""

from __future__ import annotations

import asyncio

import pytest

from culture.console.client import ChatMessage, ConsoleIRCClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_console_client(server, nick: str = "testserv-console") -> ConsoleIRCClient:
    """Create a ConsoleIRCClient pointed at the test server."""
    return ConsoleIRCClient(
        host="127.0.0.1",
        port=server.config.port,
        nick=nick,
    )


# ---------------------------------------------------------------------------
# Basic connect / disconnect
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_and_register(server):
    """Client connects and connected flag is True after welcome."""
    client = make_console_client(server)
    await client.connect()
    try:
        assert client.connected is True
        assert client.nick in server.clients
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_disconnect_sets_connected_false(server):
    """Disconnect closes the connection and sets connected = False."""
    client = make_console_client(server)
    await client.connect()
    assert client.connected is True
    await client.disconnect()
    assert client.connected is False


# ---------------------------------------------------------------------------
# Join / part
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_join_channel(server):
    """join() adds the channel to joined_channels."""
    client = make_console_client(server)
    await client.connect()
    try:
        await client.join("#general")
        assert "#general" in client.joined_channels
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_part_channel(server):
    """part() removes the channel from joined_channels."""
    client = make_console_client(server)
    await client.connect()
    try:
        await client.join("#general")
        assert "#general" in client.joined_channels
        await client.part("#general")
        assert "#general" not in client.joined_channels
    finally:
        await client.disconnect()


# ---------------------------------------------------------------------------
# send_privmsg / drain_messages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_privmsg(server, make_client):
    """send_privmsg delivers a message that another client can receive."""
    client = make_console_client(server)
    await client.connect()
    await client.join("#general")
    await asyncio.sleep(0.1)

    human = await make_client(nick="testserv-human", user="human")
    await human.send("JOIN #general")
    await human.recv_all(timeout=0.3)

    await client.send_privmsg("#general", "hello from console")
    response = await human.recv(timeout=2.0)
    assert "hello from console" in response

    await client.disconnect()


@pytest.mark.asyncio
async def test_drain_messages_returns_list(server, make_client):
    """drain_messages() returns a list (empty or with ChatMessage items)."""
    client = make_console_client(server)
    await client.connect()
    await client.join("#general")
    await asyncio.sleep(0.1)

    result = client.drain_messages()
    assert isinstance(result, list)

    await client.disconnect()


@pytest.mark.asyncio
async def test_drain_messages_buffers_incoming(server, make_client):
    """Incoming PRIVMSG is buffered and returned by drain_messages()."""
    client = make_console_client(server)
    await client.connect()
    await client.join("#general")
    await asyncio.sleep(0.1)

    sender = await make_client(nick="testserv-sender", user="sender")
    await sender.send("JOIN #general")
    await sender.recv_all(timeout=0.3)

    await sender.send("PRIVMSG #general :hi console")
    await asyncio.sleep(0.2)

    msgs = client.drain_messages()
    assert any(
        m.channel == "#general" and m.nick == "testserv-sender" and m.text == "hi console"
        for m in msgs
    )

    await client.disconnect()


@pytest.mark.asyncio
async def test_drain_messages_clears_buffer(server, make_client):
    """drain_messages() clears the buffer so the second call returns empty."""
    client = make_console_client(server)
    await client.connect()
    await client.join("#general")
    await asyncio.sleep(0.1)

    sender = await make_client(nick="testserv-clearsender", user="clearsender")
    await sender.send("JOIN #general")
    await sender.recv_all(timeout=0.3)

    await sender.send("PRIVMSG #general :one message")
    await asyncio.sleep(0.2)

    first = client.drain_messages()
    assert len(first) >= 1

    second = client.drain_messages()
    assert second == []

    await client.disconnect()


# ---------------------------------------------------------------------------
# ChatMessage dataclass
# ---------------------------------------------------------------------------


def test_chat_message_has_timestamp():
    """ChatMessage auto-populates timestamp when not provided."""
    msg = ChatMessage(channel="#test", nick="ori", text="hello")
    assert msg.timestamp > 0.0


def test_chat_message_explicit_timestamp():
    """ChatMessage accepts an explicit timestamp."""
    msg = ChatMessage(channel="#test", nick="ori", text="hello", timestamp=1234567890.0)
    assert msg.timestamp == pytest.approx(1234567890.0)


# ---------------------------------------------------------------------------
# list_channels
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_channels_after_join(server):
    """list_channels() returns the channel after it has been joined."""
    client = make_console_client(server)
    await client.connect()
    await client.join("#listtest")
    await asyncio.sleep(0.1)

    channels = await client.list_channels()
    assert isinstance(channels, list)
    assert "#listtest" in channels

    await client.disconnect()


@pytest.mark.asyncio
async def test_list_channels_empty(server):
    """list_channels() returns an empty list when no channels exist."""
    client = make_console_client(server)
    await client.connect()

    channels = await client.list_channels()
    assert channels == []

    await client.disconnect()


# ---------------------------------------------------------------------------
# who
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_who_returns_own_nick(server):
    """who() on a channel the client has joined includes the client's own nick."""
    client = make_console_client(server, nick="testserv-whotest")
    await client.connect()
    await client.join("#whotest")
    await asyncio.sleep(0.1)

    entries = await client.who("#whotest")
    assert isinstance(entries, list)
    nicks = [e["nick"] for e in entries]
    assert "testserv-whotest" in nicks

    await client.disconnect()


@pytest.mark.asyncio
async def test_who_entries_have_expected_keys(server):
    """who() entries include the standard IRC WHO fields."""
    client = make_console_client(server, nick="testserv-whokeys")
    await client.connect()
    await client.join("#whokeys")
    await asyncio.sleep(0.1)

    entries = await client.who("#whokeys")
    assert len(entries) >= 1
    entry = entries[0]
    for key in ("nick", "user", "host", "server", "flags"):
        assert key in entry, f"Missing key: {key}"

    await client.disconnect()


# ---------------------------------------------------------------------------
# history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_history_returns_list(server):
    """history() returns a list (even for a channel with no messages)."""
    client = make_console_client(server)
    await client.connect()
    await client.join("#histtest")
    await asyncio.sleep(0.1)

    entries = await client.history("#histtest")
    assert isinstance(entries, list)

    await client.disconnect()


@pytest.mark.asyncio
async def test_history_returns_messages(server, make_client):
    """history() returns messages sent before the query."""
    client = make_console_client(server, nick="testserv-histconsole")
    await client.connect()
    await client.join("#histchan")
    await asyncio.sleep(0.1)

    sender = await make_client(nick="testserv-histsender", user="histsender")
    await sender.send("JOIN #histchan")
    await sender.recv_all(timeout=0.3)

    await sender.send("PRIVMSG #histchan :history test message")
    await asyncio.sleep(0.1)

    entries = await client.history("#histchan", limit=10)
    assert isinstance(entries, list)
    assert any(e.get("text") == "history test message" for e in entries)

    await client.disconnect()
