"""Tests for the worker daemon's boss permission-notice DM (boss-agent layer)."""

from __future__ import annotations

from tests._sdk_stub import install_claude_sdk_stub

install_claude_sdk_stub()

import json  # noqa: E402
import os  # noqa: E402
from unittest.mock import AsyncMock, MagicMock  # noqa: E402

import pytest  # noqa: E402

import culture.clients.claude.daemon as daemon_mod  # noqa: E402
from culture.clients.claude.config import AgentConfig, DaemonConfig  # noqa: E402
from culture.clients.claude.daemon import AgentDaemon  # noqa: E402


def _daemon(boss: str) -> AgentDaemon:
    config = DaemonConfig()
    agent = AgentConfig(
        nick="local-worker", directory="/tmp", channels=["#team", "#task-worker"], boss=boss
    )
    return AgentDaemon(config, agent, socket_dir="/tmp", skip_claude=True)


class TestOnPermRequest:
    @pytest.mark.asyncio
    async def test_dms_boss_when_configured(self):
        d = _daemon(boss="local-boss")
        d._transport = AsyncMock()
        await d._on_perm_request(
            {"id": "req-1", "tool_name": "Edit", "input": {"file_path": "/etc/hosts"}}
        )
        d._transport.send_privmsg.assert_awaited_once()
        target, text = d._transport.send_privmsg.await_args.args
        assert target == "local-boss"
        assert "req-1" in text
        assert "Edit" in text
        assert "/etc/hosts" in text

    @pytest.mark.asyncio
    async def test_no_boss_sends_nothing(self):
        d = _daemon(boss="")
        d._transport = AsyncMock()
        await d._on_perm_request({"id": "req-2", "tool_name": "Bash", "input": {"command": "ls"}})
        d._transport.send_privmsg.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_transport_sends_nothing(self):
        d = _daemon(boss="local-boss")
        d._transport = None
        # Must not raise even though there's a boss but no transport yet.
        await d._on_perm_request({"id": "req-3", "tool_name": "Bash", "input": {"command": "ls"}})


class TestIdleWatchdog:
    """The watchdog catches three classes of silent worker:

    * never_briefed — no mention/poll/invite ever landed within grace
    * stalled_pre_engagement — brief landed, no AssistantMessage in STALL grace
    * stalled_post_engagement — engaged, then no new AssistantMessage in grace

    Tests drive ``_watchdog_tick`` directly (the loop body) so the watchdog can
    be exercised deterministically without sleeping for ``WATCHDOG_POLL_SECONDS``.
    """

    @staticmethod
    def _wd_state() -> dict:
        return {"warned_state": None}

    @pytest.mark.asyncio
    async def test_dms_boss_when_never_engaged(self, tmp_path, monkeypatch):
        import time as _time

        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        monkeypatch.setattr(daemon_mod, "IDLE_GRACE_SECONDS", 0)
        d = _daemon(boss="local-boss")
        d._transport = AsyncMock()
        d._agent_runner = AsyncMock()
        d._engaged = False
        await d._watchdog_tick(_time.time() - 1, self._wd_state())
        d._transport.send_privmsg.assert_awaited_once()
        target, text = d._transport.send_privmsg.await_args.args
        assert target == "local-boss"
        assert "idle" in text.lower() and "local-worker" in text

    @pytest.mark.asyncio
    async def test_no_dm_when_engaged_and_recently_active(self, tmp_path, monkeypatch):
        import time as _time

        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        monkeypatch.setattr(daemon_mod, "IDLE_GRACE_SECONDS", 0)
        monkeypatch.setattr(daemon_mod, "STALL_GRACE_SECONDS", 300)
        d = _daemon(boss="local-boss")
        d._transport = AsyncMock()
        d._agent_runner = AsyncMock()
        d._engaged = True
        d._last_assistant_message_at = _time.time()  # just produced a turn
        await d._watchdog_tick(_time.time() - 1, self._wd_state())
        d._transport.send_privmsg.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_dm_when_activated_within_stall_grace(self, tmp_path, monkeypatch):
        # A worker that received its brief recently (within STALL grace) but
        # hasn't finished its first turn yet (slow model, extended thinking,
        # long first tool call) is busy, not stalled.
        import time as _time

        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        monkeypatch.setattr(daemon_mod, "IDLE_GRACE_SECONDS", 0)
        monkeypatch.setattr(daemon_mod, "STALL_GRACE_SECONDS", 300)
        d = _daemon(boss="local-boss")
        d._transport = AsyncMock()
        d._agent_runner = AsyncMock()
        d._engaged = False
        d._last_activation = _time.time() - 5  # briefed 5s ago, mid-first-turn
        await d._watchdog_tick(_time.time() - 1, self._wd_state())
        d._transport.send_privmsg.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dms_boss_when_stalled_pre_engagement(self, tmp_path, monkeypatch):
        # Brief landed but no AssistantMessage ever produced — SDK hang.
        import time as _time

        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        monkeypatch.setattr(daemon_mod, "IDLE_GRACE_SECONDS", 0)
        monkeypatch.setattr(daemon_mod, "STALL_GRACE_SECONDS", 1)
        d = _daemon(boss="local-boss")
        d._transport = AsyncMock()
        d._agent_runner = AsyncMock()
        d._engaged = False
        d._last_activation = _time.time() - 60  # briefed 60s ago, no output
        await d._watchdog_tick(_time.time() - 1, self._wd_state())
        d._transport.send_privmsg.assert_awaited_once()
        target, text = d._transport.send_privmsg.await_args.args
        assert target == "local-boss"
        assert "stall" in text.lower() and "received" in text.lower()

    @pytest.mark.asyncio
    async def test_dms_boss_when_stalled_post_engagement(self, tmp_path, monkeypatch):
        # Worker engaged then went silent — the engaged-then-silent class the
        # old one-shot watchdog could not see.
        import time as _time

        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        monkeypatch.setattr(daemon_mod, "IDLE_GRACE_SECONDS", 0)
        monkeypatch.setattr(daemon_mod, "STALL_GRACE_SECONDS", 1)
        d = _daemon(boss="local-boss")
        d._transport = AsyncMock()
        d._agent_runner = AsyncMock()
        d._engaged = True
        d._last_assistant_message_at = _time.time() - 60  # last turn 60s ago
        await d._watchdog_tick(_time.time() - 1, self._wd_state())
        d._transport.send_privmsg.assert_awaited_once()
        target, text = d._transport.send_privmsg.await_args.args
        assert target == "local-boss"
        assert "stall" in text.lower() and "engaged" in text.lower()

    @pytest.mark.asyncio
    async def test_warns_once_per_state(self, tmp_path, monkeypatch):
        # Calling tick twice in the same state must DM the boss only once.
        import time as _time

        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        monkeypatch.setattr(daemon_mod, "IDLE_GRACE_SECONDS", 0)
        d = _daemon(boss="local-boss")
        d._transport = AsyncMock()
        d._agent_runner = AsyncMock()
        d._engaged = False
        state = self._wd_state()
        await d._watchdog_tick(_time.time() - 1, state)
        await d._watchdog_tick(_time.time() - 1, state)
        assert d._transport.send_privmsg.await_count == 1

    @pytest.mark.asyncio
    async def test_warns_again_on_state_change(self, tmp_path, monkeypatch):
        # never_briefed → activation arrives → eventually stalled_pre_engagement.
        # Two distinct DMs (one per state).
        import time as _time

        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        monkeypatch.setattr(daemon_mod, "IDLE_GRACE_SECONDS", 0)
        monkeypatch.setattr(daemon_mod, "STALL_GRACE_SECONDS", 1)
        d = _daemon(boss="local-boss")
        d._transport = AsyncMock()
        d._agent_runner = AsyncMock()
        d._engaged = False
        state = self._wd_state()
        await d._watchdog_tick(_time.time() - 1, state)  # never_briefed
        d._last_activation = _time.time() - 60  # now stalled-pre-engagement
        await d._watchdog_tick(_time.time() - 1, state)
        assert d._transport.send_privmsg.await_count == 2
        first = d._transport.send_privmsg.await_args_list[0].args[1].lower()
        second = d._transport.send_privmsg.await_args_list[1].args[1].lower()
        assert "idle" in first and "stall" in second

    @pytest.mark.asyncio
    async def test_no_dm_when_paused(self, tmp_path, monkeypatch):
        # Paused workers don't fire; returns True to stop the loop.
        import time as _time

        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        monkeypatch.setattr(daemon_mod, "IDLE_GRACE_SECONDS", 0)
        d = _daemon(boss="local-boss")
        d._transport = AsyncMock()
        d._agent_runner = AsyncMock()
        d._engaged = False
        d._paused = True
        stop = await d._watchdog_tick(_time.time() - 1, self._wd_state())
        assert stop is True
        d._transport.send_privmsg.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_dm_when_runner_dead(self, tmp_path, monkeypatch):
        import time as _time

        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        monkeypatch.setattr(daemon_mod, "IDLE_GRACE_SECONDS", 0)
        d = _daemon(boss="local-boss")
        d._transport = AsyncMock()
        runner = AsyncMock()
        # is_running is a *sync* method in production; override the
        # AsyncMock-generated coroutine attribute with a MagicMock that
        # returns the actual bool.
        runner.is_running = MagicMock(return_value=False)
        d._agent_runner = runner
        d._engaged = False
        stop = await d._watchdog_tick(_time.time() - 1, self._wd_state())
        assert stop is True
        d._transport.send_privmsg.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_engaged_message_resets_stall_timer(self, tmp_path, monkeypatch):
        # The unified watchdog reads _last_assistant_message_at; verify
        # _on_agent_message sets it (so the post-engagement tracker drives correctly).
        import time as _time

        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        d = _daemon(boss="local-boss")
        d._supervisor = None
        assert d._last_assistant_message_at is None
        t0 = _time.time()
        await d._on_agent_message({"type": "assistant", "text": "hi", "tool_uses": []})
        assert d._last_assistant_message_at is not None
        assert d._last_assistant_message_at >= t0

    @pytest.mark.asyncio
    async def test_engagement_flag_and_engaged_record_on_first_turn(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        d = _daemon(boss="local-boss")
        d._supervisor = None
        assert d._engaged is False
        await d._on_agent_message({"type": "assistant", "text": "hi", "tool_uses": []})
        await d._on_agent_message({"type": "assistant", "text": "more", "tool_uses": []})
        assert d._engaged is True
        # `engaged` is recorded exactly once (first turn), so the dashboard idle
        # signal clears authoritatively without depending on audit size.
        log_path = os.path.join(str(tmp_path), "daemon-log", "local-worker.jsonl")
        with open(log_path, encoding="utf-8") as f:
            actions = [json.loads(line)["action"] for line in f if line.strip()]
        assert actions.count("engaged") == 1

    @pytest.mark.asyncio
    async def test_poll_dispatch_counts_as_activation(self, tmp_path, monkeypatch):
        # A worker driven by the channel poll (boss posts task context WITHOUT an
        # @mention) must count as activated, so it isn't falsely flagged idle.
        from culture.clients.claude.message_buffer import MessageBuffer

        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        d = _daemon(boss="local-boss")
        d._agent_runner = AsyncMock()
        d._buffer = MessageBuffer()
        d._buffer.add("#task-worker", "local-boss", "here is the task context (no mention)")
        assert d._last_activation is None
        d._send_channel_poll("#task-worker")
        assert d._last_activation is not None


class TestPermInputPreview:
    def test_bash_preview(self):
        assert (
            AgentDaemon._perm_input_preview("Bash", {"command": "git push origin main"})
            == "git push origin main"
        )

    def test_edit_preview(self):
        assert AgentDaemon._perm_input_preview("Write", {"file_path": "/a/b.py"}) == "/a/b.py"

    def test_mcp_preview_is_json(self):
        out = AgentDaemon._perm_input_preview("mcp__gmail__send", {"to": "x@y.z"})
        assert "x@y.z" in out

    def test_preview_truncated_to_80(self):
        long_cmd = "echo " + "a" * 200
        out = AgentDaemon._perm_input_preview("Bash", {"command": long_cmd})
        assert len(out) <= 80
