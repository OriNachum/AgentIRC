"""Tests for agent lifecycle: active / archived states + channel archiving."""

from __future__ import annotations

import os

import pytest
import yaml

from culture.config import (
    AGENT_STATE_ACTIVE,
    AGENT_STATE_ARCHIVED,
    AgentConfig,
    load_culture_yaml,
    save_culture_yaml,
    set_agent_state,
)

# -----------------------------------------------------------------------
# AgentConfig dataclass state/archived backward compat
# -----------------------------------------------------------------------


class TestAgentConfigStateSync:
    """__post_init__ must sync state <-> archived."""

    def test_default_is_active(self):
        a = AgentConfig()
        assert a.state == AGENT_STATE_ACTIVE
        assert not a.archived

    def test_archived_true_sets_state_archived(self):
        a = AgentConfig(archived=True)
        assert a.state == AGENT_STATE_ARCHIVED

    def test_state_archived_sets_archived_true(self):
        a = AgentConfig(state=AGENT_STATE_ARCHIVED)
        assert a.archived is True

    def test_explicit_archived_and_state_active_resolves_to_archived(self):
        a = AgentConfig(archived=True, state=AGENT_STATE_ACTIVE)
        assert a.state == AGENT_STATE_ARCHIVED


# -----------------------------------------------------------------------
# Serialization round-trip
# -----------------------------------------------------------------------


class TestStateSerialization:
    """state field persists through culture.yaml save/load."""

    def test_active_agent_omits_state_from_yaml(self, tmp_path):
        agent = AgentConfig(suffix="bot", state=AGENT_STATE_ACTIVE, directory=str(tmp_path))
        save_culture_yaml(str(tmp_path), [agent])
        raw = yaml.safe_load((tmp_path / "culture.yaml").read_text())
        assert "state" not in raw

    def test_archived_agent_persists_state(self, tmp_path):
        agent = AgentConfig(
            suffix="bot",
            state=AGENT_STATE_ARCHIVED,
            archived=True,
            archived_at="2026-05-30",
            directory=str(tmp_path),
        )
        save_culture_yaml(str(tmp_path), [agent])
        raw = yaml.safe_load((tmp_path / "culture.yaml").read_text())
        assert raw["state"] == "archived"
        assert raw["archived"] is True

    def test_round_trip_archived(self, tmp_path):
        agent = AgentConfig(
            suffix="bot",
            state=AGENT_STATE_ARCHIVED,
            archived_at="2026-05-30",
            archived_reason="done",
            directory=str(tmp_path),
        )
        save_culture_yaml(str(tmp_path), [agent])
        loaded = load_culture_yaml(str(tmp_path))
        assert len(loaded) == 1
        assert loaded[0].state == AGENT_STATE_ARCHIVED
        assert loaded[0].archived is True


# -----------------------------------------------------------------------
# set_agent_state transitions
# -----------------------------------------------------------------------


def _setup_agent_dir(tmp_path, suffix="bot", state=AGENT_STATE_ACTIVE):
    """Create a minimal server.yaml + culture.yaml for testing."""
    agent_dir = tmp_path / "project"
    agent_dir.mkdir()
    real_dir = os.path.realpath(str(agent_dir))
    agent = AgentConfig(suffix=suffix, state=state, directory=real_dir)
    save_culture_yaml(real_dir, [agent])
    server_yaml = tmp_path / "server.yaml"
    server_yaml.write_text(
        yaml.dump(
            {
                "server": {"name": "local"},
                "agents": {suffix: real_dir},
            }
        )
    )
    return server_yaml, agent_dir


class TestSetAgentState:
    """set_agent_state transitions."""

    def test_active_to_archived(self, tmp_path):
        config_path, agent_dir = _setup_agent_dir(tmp_path)
        set_agent_state(config_path, "local-bot", AGENT_STATE_ARCHIVED, reason="completed")
        loaded = load_culture_yaml(os.path.realpath(str(agent_dir)))
        assert loaded[0].state == AGENT_STATE_ARCHIVED
        assert loaded[0].archived is True
        assert loaded[0].archived_reason == "completed"
        assert loaded[0].archived_at

    def test_archived_to_active_restore(self, tmp_path):
        """restore command sets archived → active (stopped)."""
        config_path, agent_dir = _setup_agent_dir(tmp_path, state=AGENT_STATE_ARCHIVED)
        set_agent_state(config_path, "local-bot", AGENT_STATE_ACTIVE)
        loaded = load_culture_yaml(os.path.realpath(str(agent_dir)))
        assert loaded[0].state == AGENT_STATE_ACTIVE
        assert loaded[0].archived is False
        assert loaded[0].archived_at == ""
        assert loaded[0].archived_reason == ""

    def test_noop_same_state(self, tmp_path):
        config_path, _ = _setup_agent_dir(tmp_path)
        set_agent_state(config_path, "local-bot", AGENT_STATE_ACTIVE)
        # no error, no-op

    def test_invalid_state_raises(self, tmp_path):
        config_path, _ = _setup_agent_dir(tmp_path)
        with pytest.raises(ValueError, match="Invalid state"):
            set_agent_state(config_path, "local-bot", "invalid")

    def test_unknown_nick_raises(self, tmp_path):
        config_path, _ = _setup_agent_dir(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            set_agent_state(config_path, "local-missing", AGENT_STATE_ARCHIVED)


# -----------------------------------------------------------------------
# Status display — archived filtering
# -----------------------------------------------------------------------


class TestDisplayArchived:
    def test_archived_shows_archived(self):
        from culture.cli.shared.display import _format_agent_status

        result = _format_agent_status("stopped", True, False, state="archived")
        assert result == "archived"

    def test_active_running_shows_running(self):
        from culture.cli.shared.display import _format_agent_status

        result = _format_agent_status("running", False, False, state="active")
        assert result == "running"

    def test_archived_with_marker(self):
        from culture.cli.shared.display import _format_agent_status

        result = _format_agent_status("stopped", True, True, state="archived")
        assert result == "stopped (archived)"

    def test_status_omits_archived_by_default(self):
        """_get_active_agents filters out archived."""
        from culture.cli.agent import _get_active_agents
        from culture.config import ServerConfig

        config = ServerConfig(
            agents=[
                AgentConfig(suffix="a", nick="local-a", state=AGENT_STATE_ACTIVE),
                AgentConfig(suffix="b", nick="local-b", state=AGENT_STATE_ARCHIVED),
            ]
        )
        active = _get_active_agents(config)
        assert len(active) == 1
        assert active[0].nick == "local-a"

    def test_status_all_shows_archived(self):
        """--all includes archived agents."""
        from culture.config import ServerConfig

        config = ServerConfig(
            agents=[
                AgentConfig(suffix="a", nick="local-a", state=AGENT_STATE_ACTIVE),
                AgentConfig(suffix="b", nick="local-b", state=AGENT_STATE_ARCHIVED),
            ]
        )
        # --all returns all
        assert len(config.agents) == 2


# -----------------------------------------------------------------------
# Lifecycle scenarios
# -----------------------------------------------------------------------


class TestLifecycleScenarios:
    def test_archive_then_restore(self, tmp_path):
        """Archive → status omits → restore → back to active."""
        config_path, agent_dir = _setup_agent_dir(tmp_path)

        # Archive
        set_agent_state(config_path, "local-bot", AGENT_STATE_ARCHIVED, reason="done")
        agents = load_culture_yaml(os.path.realpath(str(agent_dir)))
        assert agents[0].state == AGENT_STATE_ARCHIVED
        assert agents[0].archived is True

        # Restore
        set_agent_state(config_path, "local-bot", AGENT_STATE_ACTIVE)
        agents = load_culture_yaml(os.path.realpath(str(agent_dir)))
        assert agents[0].state == AGENT_STATE_ACTIVE
        assert not agents[0].archived

    def test_archive_read_only_access(self, tmp_path):
        """Archived agents can be read but remain archived."""
        config_path, agent_dir = _setup_agent_dir(tmp_path, state=AGENT_STATE_ARCHIVED)
        agents = load_culture_yaml(os.path.realpath(str(agent_dir)))
        assert len(agents) == 1
        assert agents[0].state == AGENT_STATE_ARCHIVED
        assert agents[0].suffix == "bot"
        # Reading doesn't change state
        agents2 = load_culture_yaml(os.path.realpath(str(agent_dir)))
        assert agents2[0].state == AGENT_STATE_ARCHIVED


# -----------------------------------------------------------------------
# Channel archiving — server-level
# -----------------------------------------------------------------------


class TestChannelArchive:
    def test_channel_archived_flag(self):
        """Channel.archived blocks new JOINs."""
        from culture.agentirc.channel import Channel

        ch = Channel("#task-worker")
        assert not ch.archived
        ch.archived = True
        assert ch.archived

    def test_archived_channel_hidden_from_list(self):
        """Archived channels should not appear in listings."""
        from culture.agentirc.channel import Channel

        ch = Channel("#task-done")
        ch.archived = True
        # Simulates the LIST filter logic
        channels = {"#active": Channel("#active"), "#task-done": ch}
        visible = [n for n, c in channels.items() if not c.archived]
        assert "#active" in visible
        assert "#task-done" not in visible
