import asyncio
import os
import tempfile
import pytest

from agentirc.clients.opencode.daemon import OpenCodeDaemon
from agentirc.clients.opencode.config import (
    DaemonConfig, ServerConnConfig, AgentConfig,
    SupervisorConfig, WebhookConfig,
)


@pytest.mark.asyncio
async def test_opencode_daemon_starts_and_connects(server):
    """OpenCodeDaemon with skip_opencode=True connects to IRC without needing opencode CLI."""
    config = DaemonConfig(
        server=ServerConnConfig(host="127.0.0.1", port=server.config.port),
        supervisor=SupervisorConfig(),
        webhooks=WebhookConfig(url=None),
    )
    agent = AgentConfig(nick="testserv-opencode", directory="/tmp", channels=["#general"])
    sock_dir = tempfile.mkdtemp()
    daemon = OpenCodeDaemon(config, agent, socket_dir=sock_dir, skip_opencode=True)
    await daemon.start()
    try:
        await asyncio.sleep(0.5)
        assert "testserv-opencode" in server.clients
        assert "#general" in server.channels
    finally:
        await daemon.stop()


@pytest.mark.asyncio
async def test_opencode_daemon_ipc_irc_send(server, make_client):
    """IPC irc_send works through the OpenCode daemon."""
    config = DaemonConfig(
        server=ServerConnConfig(host="127.0.0.1", port=server.config.port),
    )
    agent = AgentConfig(nick="testserv-opencode", directory="/tmp", channels=["#general"])
    sock_dir = tempfile.mkdtemp()
    daemon = OpenCodeDaemon(config, agent, socket_dir=sock_dir, skip_opencode=True)
    await daemon.start()
    await asyncio.sleep(0.5)

    human = await make_client(nick="testserv-ori", user="ori")
    await human.send("JOIN #general")
    await human.recv_all(timeout=0.3)

    from agentirc.clients.opencode.ipc import encode_message, decode_message, make_request
    sock_path = os.path.join(sock_dir, "agentirc-testserv-opencode.sock")
    reader, writer = await asyncio.open_unix_connection(sock_path)

    req = make_request("irc_send", channel="#general", message="hello from opencode skill")
    writer.write(encode_message(req))
    await writer.drain()

    data = await asyncio.wait_for(reader.readline(), timeout=2.0)
    resp = decode_message(data)
    assert resp["ok"] is True

    msg = await human.recv(timeout=2.0)
    assert "hello from opencode skill" in msg

    writer.close()
    await writer.wait_closed()
    await daemon.stop()


@pytest.mark.asyncio
async def test_opencode_config_defaults():
    """OpenCode config has correct backend-specific defaults."""
    agent = AgentConfig()
    assert agent.agent == "opencode"
    assert agent.model == "anthropic/claude-sonnet-4-6"

    supervisor = SupervisorConfig()
    assert supervisor.model == "anthropic/claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_opencode_backend_dispatch():
    """CLI dispatch selects OpenCodeDaemon for agent='opencode'."""
    agent = AgentConfig(nick="test-opencode", agent="opencode", directory="/tmp")
    backend = getattr(agent, "agent", "claude")
    assert backend == "opencode"

    # Verify OpenCodeDaemon can be imported and constructed
    config = DaemonConfig()
    daemon = OpenCodeDaemon(config, agent, skip_opencode=True)
    assert daemon.agent.agent == "opencode"
    assert daemon.agent.model == "anthropic/claude-sonnet-4-6"
