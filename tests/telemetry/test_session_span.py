"""Tests for #290: Client.handle session span + irc.join/irc.part spans."""

from __future__ import annotations

import asyncio

import pytest


async def _wait_for_span(exporter, name: str, timeout: float = 1.0) -> None:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if any(s.name == name for s in exporter.get_finished_spans()):
            return
        await asyncio.sleep(0.02)


def _spans_with_name(exporter, name):
    return [s for s in exporter.get_finished_spans() if s.name == name]


@pytest.mark.asyncio
async def test_client_session_span_records_remote_addr_and_nick(
    tracing_exporter, server, make_client
):
    """irc.client.session span carries remote_addr and (after NICK) nick."""
    tracing_exporter.clear()

    client = await make_client(nick="testserv-alice", user="alice")
    # Connection is open. Inspect the live span via the Client object on
    # the server side (client is IRCTestClient — look up via server.clients).
    assert "testserv-alice" in server.clients, "server did not register nick"
    server_side_clients = server.clients
    server_client = server_side_clients["testserv-alice"]
    span = server_client._session_span
    assert span is not None
    attrs = dict(span.attributes or {})
    assert attrs.get("irc.client.nick") == "testserv-alice"
    remote_addr = attrs.get("irc.client.remote_addr", "")
    assert ":" in remote_addr  # "ip:port" shape

    # Now close — span should finish and land in exporter.
    await client.close()
    # Allow teardown.
    for _ in range(50):
        if "testserv-alice" not in server.clients:
            break
        await asyncio.sleep(0.05)
    await asyncio.sleep(0.1)

    finished = _spans_with_name(tracing_exporter, "irc.client.session")
    assert finished, "no finished irc.client.session span recorded"
    last = finished[-1]
    last_attrs = dict(last.attributes or {})
    assert last_attrs.get("irc.client.nick") == "testserv-alice"
    assert ":" in last_attrs.get("irc.client.remote_addr", "")


@pytest.mark.asyncio
async def test_join_span_records_channel_and_nick(tracing_exporter, server, make_client):
    tracing_exporter.clear()
    client = await make_client(nick="testserv-bob", user="bob")
    await client.send("JOIN #join-test")
    await client.recv_all(timeout=0.5)
    await _wait_for_span(tracing_exporter, "irc.join")

    spans = _spans_with_name(tracing_exporter, "irc.join")
    assert spans, "no irc.join span recorded"
    span = spans[-1]
    attrs = dict(span.attributes or {})
    assert attrs.get("irc.channel") == "#join-test"
    assert attrs.get("irc.client.nick") == "testserv-bob"


@pytest.mark.asyncio
async def test_part_span_records_channel_and_nick(tracing_exporter, server, make_client):
    tracing_exporter.clear()
    client = await make_client(nick="testserv-carol", user="carol")
    await client.send("JOIN #part-test")
    await client.recv_all(timeout=0.5)
    await client.send("PART #part-test :bye")
    await client.recv_all(timeout=0.5)
    await _wait_for_span(tracing_exporter, "irc.part")

    spans = _spans_with_name(tracing_exporter, "irc.part")
    assert spans, "no irc.part span recorded"
    span = spans[-1]
    attrs = dict(span.attributes or {})
    assert attrs.get("irc.channel") == "#part-test"
    assert attrs.get("irc.client.nick") == "testserv-carol"
