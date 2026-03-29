"""Tests for daemon IPC status, pause, and resume handlers."""

import asyncio
import pytest

from agentirc.clients.claude.config import AgentConfig, DaemonConfig
from agentirc.clients.claude.daemon import AgentDaemon
from agentirc.clients.claude.ipc import make_request


@pytest.fixture
def daemon():
    config = DaemonConfig()
    agent = AgentConfig(
        nick="test-agent",
        agent="claude",
        directory="/tmp/test",
        channels=["#general"],
    )
    return AgentDaemon(config, agent, skip_claude=True)


@pytest.mark.asyncio
async def test_ipc_status_initial(daemon):
    """Status should report idle and not paused initially."""
    resp = await daemon._ipc_status("req-1")
    assert resp["ok"] is True
    data = resp["data"]
    assert data["paused"] is False
    assert data["activity"] == "idle"
    assert data["description"] == "nothing"
    assert data["turn_count"] == 0
    assert data["last_activation"] is None


@pytest.mark.asyncio
async def test_ipc_pause(daemon):
    """Pause should set paused flag."""
    resp = await daemon._ipc_pause("req-2")
    assert resp["ok"] is True
    assert daemon._paused is True

    status = await daemon._ipc_status("req-3")
    assert status["data"]["paused"] is True
    assert status["data"]["activity"] == "paused"
    assert status["data"]["description"] == "paused"


@pytest.mark.asyncio
async def test_ipc_resume(daemon):
    """Resume should clear paused flag."""
    daemon._paused = True
    resp = await daemon._ipc_resume("req-4")
    assert resp["ok"] is True
    assert daemon._paused is False

    status = await daemon._ipc_status("req-5")
    assert status["data"]["paused"] is False
    assert status["data"]["activity"] == "idle"
    assert status["data"]["description"] == "nothing"


def test_on_mention_ignored_when_paused(daemon):
    """Mentions should be ignored when paused."""
    daemon._paused = True
    daemon._on_mention("#general", "someone", "hello")
    assert daemon._last_activation is None


def test_sleep_schedule_parsing(daemon):
    """Sleep schedule should parse valid HH:MM format."""
    result = daemon._parse_sleep_schedule()
    assert result is not None
    sleep_min, wake_min = result
    assert sleep_min == 23 * 60  # 23:00
    assert wake_min == 8 * 60   # 08:00


def test_sleep_schedule_invalid():
    """Invalid sleep schedule should return None."""
    config = DaemonConfig(sleep_start="invalid", sleep_end="08:00")
    agent = AgentConfig(nick="test", directory="/tmp")
    d = AgentDaemon(config, agent, skip_claude=True)
    assert d._parse_sleep_schedule() is None


@pytest.mark.asyncio
async def test_on_agent_message_captures_activity(daemon):
    """Agent messages should be captured for status reporting."""
    msg = {"type": "assistant", "content": [{"type": "text", "text": "Working on fixing tests"}]}
    await daemon._on_agent_message(msg)
    assert daemon._last_activity_text == "Working on fixing tests"

    status = await daemon._ipc_status("req-6")
    assert status["data"]["description"] == "Working on fixing tests"


@pytest.mark.asyncio
async def test_describe_activity_truncates(daemon):
    """Long activity text should be truncated."""
    long_text = "x" * 200
    daemon._last_activity_text = long_text
    desc = daemon._describe_activity()
    assert len(desc) <= 120
    assert desc.endswith("...")
