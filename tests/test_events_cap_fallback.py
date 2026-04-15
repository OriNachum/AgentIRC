"""CAP negotiation for message-tags + plain-body fallback for non-tag clients."""

import asyncio

import pytest


@pytest.mark.asyncio
async def test_cap_ls_lists_message_tags(server, make_client):
    c = await make_client()
    await c.send("CAP LS")
    line = await c.recv()
    assert "message-tags" in line


@pytest.mark.asyncio
async def test_cap_req_ack(server, make_client):
    c = await make_client()
    await c.send("CAP LS")
    await c.recv()
    await c.send("CAP REQ :message-tags")
    line = await c.recv()
    assert "ACK" in line
    assert "message-tags" in line


@pytest.mark.asyncio
async def test_non_tag_client_receives_plain_privmsg(server, make_client):
    """A client that never REQs message-tags should not receive @tag blocks."""
    c = await make_client(nick="testserv-alice", user="alice")
    # Do not send CAP REQ. Server will strip tags.
    # Force the server to emit a tagged PRIVMSG by triggering an event.
    # Use `JOIN #testchan`, which will surface as tagged PRIVMSG once
    # events are wired through (later tasks). For now, the inverse check:
    # just verify that lines arrive without a leading '@' when the
    # client has not opted in.
    await c.send("JOIN #testchan")
    lines = await c.recv_all(timeout=1.0)
    for line in lines:
        assert not line.startswith("@"), f"unexpected tagged line: {line}"
    join_lines = [l for l in lines if "JOIN" in l]
    assert len(join_lines) > 0
