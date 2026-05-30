"""Model + thinking inheritance: a spawned worker imitates its parent (boss)'s
RUNTIME model and thinking — read from the boss's daemon-log, not its yaml,
so there are no hardcoded model strings anywhere in the inheritance chain.
The SDK picks the current Claude when no model is set; that choice lands in
the boss's agent_start daemon-log record and is propagated forward.
"""

from __future__ import annotations

import json

from tests._sdk_stub import install_claude_sdk_stub

install_claude_sdk_stub()

import os  # noqa: E402

import yaml  # noqa: E402

import culture.cli.boss as boss  # noqa: E402


def _write_boss_daemon_log(home, boss_nick="local-boss", model="", thinking=""):
    """Write a synthetic ``agent_start`` record to the boss's daemon-log. This
    is what a live boss daemon records on startup, capturing the model+thinking
    it's actually running with."""
    log_dir = os.path.join(str(home), "daemon-log")
    os.makedirs(log_dir, exist_ok=True)
    rec = {
        "ts": "2026-05-30T00:00:00.000Z",
        "nick": boss_nick,
        "action": "agent_start",
        "detail": {"model": model, "thinking": thinking, "directory": "/x"},
    }
    with open(os.path.join(log_dir, f"{boss_nick}.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def test_record_worker_writes_model_when_given(tmp_path):
    cwd = str(tmp_path)
    boss._record_worker_boss(cwd, "qa", "local-boss", model="claude-opus-4-7")
    with open(os.path.join(cwd, "culture.yaml"), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["model"] == "claude-opus-4-7"
    assert data["boss"] == "local-boss"


def test_record_worker_omits_model_when_empty(tmp_path):
    cwd = str(tmp_path)
    boss._record_worker_boss(cwd, "qa", "local-boss", model="")
    with open(os.path.join(cwd, "culture.yaml"), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "model" not in data  # falls back to the agent default, not a forced value


def test_inherited_model_does_not_clobber_existing(tmp_path):
    # Re-spawn with an INHERITED model must not overwrite a model the worker
    # already carries (operator hand-set); only an explicit --model overwrites.
    cwd = str(tmp_path)
    with open(os.path.join(cwd, "culture.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump({"suffix": "qa", "backend": "claude", "model": "claude-haiku-4-5"}, f)
    boss._record_worker_boss(
        cwd, "qa", "local-boss", model="claude-opus-4-7", overwrite_model=False
    )
    with open(os.path.join(cwd, "culture.yaml"), encoding="utf-8") as f:
        assert yaml.safe_load(f)["model"] == "claude-haiku-4-5"  # preserved


def test_explicit_model_overwrites_existing(tmp_path):
    cwd = str(tmp_path)
    with open(os.path.join(cwd, "culture.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump({"suffix": "qa", "backend": "claude", "model": "claude-haiku-4-5"}, f)
    boss._record_worker_boss(cwd, "qa", "local-boss", model="claude-opus-4-7", overwrite_model=True)
    with open(os.path.join(cwd, "culture.yaml"), encoding="utf-8") as f:
        assert yaml.safe_load(f)["model"] == "claude-opus-4-7"  # explicit --model wins


def test_record_worker_into_multi_agent_yaml(tmp_path):
    # Spawning into a dir that already holds a multi-agent culture.yaml must write
    # boss/channels into THIS worker's entry in the agents list — not top-level
    # (which the loader shadows, leaving the worker unassigned in #general).
    cwd = str(tmp_path)
    with open(os.path.join(cwd, "culture.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(
            {
                "agents": [
                    {"suffix": "ori", "backend": "claude", "channels": ["#team", "#task-ori"]},
                    {"suffix": "qa", "backend": "claude"},
                ]
            },
            f,
        )
    boss._record_worker_boss(cwd, "qa", "local-boss", model="claude-opus-4-7")
    with open(os.path.join(cwd, "culture.yaml"), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    entry = next(a for a in data["agents"] if a["suffix"] == "qa")
    assert entry["boss"] == "local-boss"
    assert entry["channels"] == ["#team", "#task-qa"]
    assert entry["model"] == "claude-opus-4-7"
    # No stray top-level single-agent fields shadowing the list.
    assert "boss" not in data and "channels" not in data and "suffix" not in data
    # The sibling entry is untouched.
    assert next(a for a in data["agents"] if a["suffix"] == "ori")["channels"] == [
        "#team",
        "#task-ori",
    ]


def test_boss_inherits_empty_when_no_daemon_log(tmp_path, monkeypatch):
    # Boss never ran → daemon-log absent → no inherited model/thinking. The
    # caller writes empty strings and the SDK picks the current Claude at the
    # worker's startup. No hardcoded fallback anywhere.
    monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
    monkeypatch.setenv("CULTURE_NICK", "local-boss")
    assert boss._boss_inherits() == ("", "")
    assert boss._boss_model() == ""


def test_boss_inherits_from_daemon_log_model(tmp_path, monkeypatch):
    # The boss daemon recorded its RUNTIME model on startup → spawn inherits
    # that exact value, not whatever the yaml might say.
    monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
    monkeypatch.setenv("CULTURE_NICK", "local-boss")
    _write_boss_daemon_log(tmp_path, model="claude-opus-4-8", thinking="")
    model, thinking = boss._boss_inherits()
    assert model == "claude-opus-4-8"
    assert thinking == ""
    # Back-compat alias.
    assert boss._boss_model() == "claude-opus-4-8"


def test_boss_inherits_both_model_and_thinking(tmp_path, monkeypatch):
    # Thinking is inherited the same way as model — workers imitate parent
    # effort level, not just parent model.
    monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
    monkeypatch.setenv("CULTURE_NICK", "local-boss")
    _write_boss_daemon_log(tmp_path, model="claude-opus-4-8", thinking="high")
    assert boss._boss_inherits() == ("claude-opus-4-8", "high")


def test_boss_inherits_uses_most_recent_agent_start(tmp_path, monkeypatch):
    # Multiple agent_start records (boss restarted) → most recent wins.
    monkeypatch.setenv("CULTURE_HOME", str(tmp_path))
    monkeypatch.setenv("CULTURE_NICK", "local-boss")
    log_dir = os.path.join(str(tmp_path), "daemon-log")
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, "local-boss.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "ts": "2026-05-29T00:00:00.000Z",
                    "nick": "local-boss",
                    "action": "agent_start",
                    "detail": {"model": "claude-opus-4-7", "thinking": "medium"},
                }
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "ts": "2026-05-29T00:05:00.000Z",
                    "nick": "local-boss",
                    "action": "agent_exit",
                    "detail": {"exit_code": 0},
                }
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "ts": "2026-05-30T00:00:00.000Z",
                    "nick": "local-boss",
                    "action": "agent_start",
                    "detail": {"model": "claude-opus-4-8", "thinking": "high"},
                }
            )
            + "\n"
        )
    assert boss._boss_inherits() == ("claude-opus-4-8", "high")


def test_record_worker_writes_thinking_too(tmp_path):
    # Inheritance covers thinking, not just model.
    cwd = str(tmp_path)
    boss._record_worker_boss(cwd, "qa", "local-boss", model="claude-opus-4-8", thinking="high")
    with open(os.path.join(cwd, "culture.yaml"), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["model"] == "claude-opus-4-8"
    assert data["thinking"] == "high"
