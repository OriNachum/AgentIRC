"""Tests for the silent-death watchdog (v8.19.8).

Closes the reliability gap surfaced during the v8.18.7 fleet ship:
worker daemons died without writing ``agent_exit`` (likely SDK CLI
``Stream closed`` propagating an uncaught exception up to the
asyncio loop). The intra-process ``_idle_watchdog`` couldn't catch
this — it only watches the boss's own SDK state, not its workers'
process liveness. The cross-process detector closes the gap by
periodically scanning owned workers' PIDs + daemon-log tails and
surfacing ``idle_warning {reason: silent_death_after_done}``.
"""

from __future__ import annotations

import json
import os

import pytest

from tests._sdk_stub import install_claude_sdk_stub

install_claude_sdk_stub()

from culture.clients.claude.daemon import AgentDaemon  # noqa: E402


def _make_daemon(tmp_path, nick="local-boss"):
    """Build a minimal AgentDaemon for unit-testing helper methods."""
    from culture.clients.claude.config import (
        AgentConfig,
        DaemonConfig,
        ServerConnConfig,
    )

    server_cfg = ServerConnConfig(host="127.0.0.1", port=6667)
    daemon_cfg = DaemonConfig(server=server_cfg)
    agent_cfg = AgentConfig(nick=nick, agent="claude", tags=["boss"])
    return AgentDaemon(daemon_cfg, agent_cfg, skip_claude=True)


def _write_daemon_log_action(home, nick, action):
    """Write a single daemon-log line for *nick* with *action* as the last record."""
    log_dir = os.path.join(str(home), "daemon-log")
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, f"{nick}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(
            json.dumps({"ts": "2026-05-30T20:00:00.000Z", "nick": nick, "action": action}) + "\n"
        )


class TestDaemonLogIndicatesCleanExit:
    """The clean-exit detector reads the daemon-log tail and returns
    True only for the explicit exit/stop markers."""

    def test_agent_exit_returns_true(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        daemon = _make_daemon(tmp_path)
        _write_daemon_log_action(tmp_path, "local-worker", "agent_start")
        _write_daemon_log_action(tmp_path, "local-worker", "engaged")
        _write_daemon_log_action(tmp_path, "local-worker", "agent_exit")
        assert daemon._daemon_log_indicates_clean_exit("local-worker") is True

    def test_agent_stop_returns_true(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        daemon = _make_daemon(tmp_path)
        _write_daemon_log_action(tmp_path, "local-worker", "agent_start")
        _write_daemon_log_action(tmp_path, "local-worker", "agent_stop")
        assert daemon._daemon_log_indicates_clean_exit("local-worker") is True

    def test_missing_log_returns_false(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        daemon = _make_daemon(tmp_path)
        # No log file ever written.
        assert daemon._daemon_log_indicates_clean_exit("never-started") is False

    def test_engaged_only_returns_false(self, tmp_path, monkeypatch):
        # Last action is ``engaged`` → process is gone but never wrote
        # exit → silent death.
        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        daemon = _make_daemon(tmp_path)
        _write_daemon_log_action(tmp_path, "local-worker", "agent_start")
        _write_daemon_log_action(tmp_path, "local-worker", "engaged")
        assert daemon._daemon_log_indicates_clean_exit("local-worker") is False

    def test_supervisor_escalation_only_returns_false(self, tmp_path, monkeypatch):
        # Real v8.18.7 fleet pattern: workers' last action was
        # ``supervisor_escalation``, then daemon died without recording
        # exit.
        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        daemon = _make_daemon(tmp_path)
        _write_daemon_log_action(tmp_path, "local-worker", "agent_start")
        _write_daemon_log_action(tmp_path, "local-worker", "engaged")
        _write_daemon_log_action(tmp_path, "local-worker", "supervisor_escalation")
        assert daemon._daemon_log_indicates_clean_exit("local-worker") is False

    def test_corrupt_jsonl_line_skipped(self, tmp_path, monkeypatch):
        # Unparseable lines must not throw; the detector keeps walking.
        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        daemon = _make_daemon(tmp_path)
        log_dir = os.path.join(str(tmp_path), "daemon-log")
        os.makedirs(log_dir, exist_ok=True)
        path = os.path.join(log_dir, "local-worker.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            f.write("not valid json\n")
            f.write(
                json.dumps(
                    {
                        "ts": "2026-05-30T20:00:00.000Z",
                        "nick": "local-worker",
                        "action": "agent_exit",
                    }
                )
                + "\n"
            )
        assert daemon._daemon_log_indicates_clean_exit("local-worker") is True


class TestSilentDeathWatchdogInit:
    """The watchdog task is started ONLY on boss-tagged agents."""

    def test_boss_tag_starts_task(self, tmp_path, monkeypatch):
        # Constructing the AgentDaemon doesn't start the task — start()
        # does (which we don't call in this unit test). Instead verify
        # the init-time field is in place so the start path can use it.
        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        daemon = _make_daemon(tmp_path)
        assert daemon._silent_death_task is None
        assert daemon._silent_death_warned == set()

    def test_non_boss_no_watchdog_state(self, tmp_path, monkeypatch):
        # Even on a non-boss agent the field exists (always-init pattern)
        # so the cleanup in stop() never KeyErrors.
        monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
        from culture.clients.claude.config import (
            AgentConfig,
            DaemonConfig,
            ServerConnConfig,
        )

        server_cfg = ServerConnConfig(host="127.0.0.1", port=6667)
        agent_cfg = AgentConfig(nick="local-worker", agent="claude", tags=[])
        daemon = AgentDaemon(DaemonConfig(server=server_cfg), agent_cfg, skip_claude=True)
        assert daemon._silent_death_task is None
        assert daemon._silent_death_warned == set()
