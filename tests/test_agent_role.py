"""Tests for the role: field on AgentConfig (v8.19.4).

The role declaration is how the orchestrator tracks who-does-what
in a channel with many agents. Set at spawn (--role flag) or in
culture.yaml directly. Surfaced in the dashboard.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from culture.cli import boss
from culture.config import AgentConfig, load_culture_yaml, save_culture_yaml


class TestAgentConfigRole:
    def test_default_role_is_empty_string(self):
        c = AgentConfig()
        assert c.role == ""

    def test_role_can_be_set(self):
        c = AgentConfig(suffix="qa", role="qa-runner")
        assert c.role == "qa-runner"

    def test_role_round_trips_through_yaml(self, tmp_path):
        agents = [AgentConfig(suffix="qa", backend="claude", role="qa-runner")]
        save_culture_yaml(str(tmp_path), agents)
        loaded = load_culture_yaml(str(tmp_path))
        assert len(loaded) == 1
        assert loaded[0].role == "qa-runner"

    def test_empty_role_not_written_to_yaml(self, tmp_path):
        # The serializer should omit the role key when it's the default
        # empty string — keeps culture.yaml files minimal for agents
        # that don't carry a role.
        agents = [AgentConfig(suffix="qa", backend="claude", role="")]
        save_culture_yaml(str(tmp_path), agents)
        with open(tmp_path / "culture.yaml", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        assert "role" not in raw

    def test_role_persisted_across_spawn(self, tmp_path):
        # _record_worker_boss should write the role when given.
        cwd = str(tmp_path)
        boss._record_worker_boss(cwd, "qa", "local-boss", model="", thinking="", role="qa-runner")
        loaded = load_culture_yaml(cwd)
        # The worker entry must carry the role.
        qa = next((a for a in loaded if a.suffix == "qa"), None)
        assert qa is not None
        assert qa.role == "qa-runner"

    def test_role_overwrites_on_respawn(self, tmp_path):
        # Re-spawning with a new role overwrites the previous one.
        cwd = str(tmp_path)
        boss._record_worker_boss(cwd, "qa", "local-boss", role="qa-runner")
        boss._record_worker_boss(cwd, "qa", "local-boss", role="qa-author")
        loaded = load_culture_yaml(cwd)
        qa = next((a for a in loaded if a.suffix == "qa"), None)
        assert qa is not None
        assert qa.role == "qa-author"

    def test_no_role_arg_preserves_existing(self, tmp_path):
        # When --role isn't passed (role=""), an existing role on the
        # worker's YAML must NOT be wiped.
        cwd = str(tmp_path)
        # Seed an existing role via yaml.
        with open(os.path.join(cwd, "culture.yaml"), "w", encoding="utf-8") as f:
            yaml.safe_dump({"suffix": "qa", "backend": "claude", "role": "qa-runner"}, f)
        boss._record_worker_boss(cwd, "qa", "local-boss", role="")
        loaded = load_culture_yaml(cwd)
        qa = next((a for a in loaded if a.suffix == "qa"), None)
        assert qa is not None
        # Role preserved since the caller passed role="".
        assert qa.role == "qa-runner"
