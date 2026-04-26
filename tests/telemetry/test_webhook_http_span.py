"""Inbound HTTP span via opentelemetry-instrumentation-aiohttp-server (Plan 7)."""

from __future__ import annotations

import pytest
import pytest_asyncio
from aiohttp import ClientSession

from culture.bots.bot_manager import BotManager
from culture.bots.config import BotConfig
from culture.bots.http_listener import HttpListener


@pytest_asyncio.fixture
async def webhook_server(server, tmp_path, monkeypatch):
    monkeypatch.setattr("culture.bots.config.BOTS_DIR", tmp_path)
    monkeypatch.setattr("culture.bots.bot.BOTS_DIR", tmp_path)
    monkeypatch.setattr("culture.bots.bot_manager.BOTS_DIR", tmp_path)

    mgr = BotManager(server)
    server.bot_manager = mgr

    listener = HttpListener(mgr, "127.0.0.1", 0)
    await listener.start()
    site = next(iter(listener._runner._sites))
    port = site._server.sockets[0].getsockname()[1]

    yield server, mgr, port

    await listener.stop()
    await mgr.stop_all()


@pytest.mark.asyncio
async def test_webhook_emits_aiohttp_server_span_parenting_bot_run(
    tracing_exporter, webhook_server
):
    server, mgr, port = webhook_server
    await mgr.create_bot(
        BotConfig(
            name="testserv-spanhook",
            owner="testserv",
            channels=[],
            template="ok {body}",
        )
    )

    async with ClientSession() as session:
        async with session.post(
            f"http://127.0.0.1:{port}/testserv-spanhook", json={"body": "x"}
        ) as resp:
            assert resp.status == 200

    spans = tracing_exporter.get_finished_spans()
    aiohttp_spans = [
        s
        for s in spans
        if s.instrumentation_scope.name == "opentelemetry.instrumentation.aiohttp_server"
    ]
    assert aiohttp_spans, [s.instrumentation_scope.name for s in spans]
    aiohttp_span = aiohttp_spans[0]

    run_spans = [s for s in spans if s.name == "bot.run"]
    assert len(run_spans) == 1
    run = run_spans[0]
    # bot.run is parented under the aiohttp server span (same trace).
    assert run.context.trace_id == aiohttp_span.context.trace_id
    assert run.parent is not None
    assert run.parent.span_id == aiohttp_span.context.span_id
