"""Brief-delivery verification: `culture boss brief` must not claim success when
the worker isn't in the channel to hear it (the false-"boss flow is live" bug).
"""

from __future__ import annotations

from tests._sdk_stub import install_claude_sdk_stub

install_claude_sdk_stub()

import argparse  # noqa: E402

import pytest  # noqa: E402

import culture.cli.boss as boss  # noqa: E402


@pytest.fixture
def as_boss(monkeypatch):
    monkeypatch.setenv("CULTURE_NICK", "local-boss")
    return monkeypatch


def test_brief_refused_when_worker_absent(as_boss):
    as_boss.setattr(boss, "_channel_members", lambda ch: ["local-boss"])  # worker not present
    sent = []
    as_boss.setattr(boss, "_boss_irc", lambda mt, **kw: sent.append((mt, kw)) or {"ok": True})
    with pytest.raises(SystemExit) as exc:
        boss._cmd_brief(argparse.Namespace(name="qa", task="do it"))
    assert exc.value.code == 1
    assert sent == []  # never sent — no false "delivered"


def test_brief_sent_when_worker_present(as_boss):
    as_boss.setattr(boss, "_channel_members", lambda ch: ["local-boss", "local-qa"])
    sent = []
    as_boss.setattr(boss, "_boss_irc", lambda mt, **kw: sent.append((mt, kw)) or {"ok": True})
    boss._cmd_brief(argparse.Namespace(name="qa", task="do it"))
    assert len(sent) == 1
    mt, kw = sent[0]
    assert mt == "irc_send"
    assert kw["channel"] == "#task-qa"
    assert kw["message"] == "@local-qa do it"  # nick-prefixed so mention fires


def test_brief_refused_when_membership_unverifiable(as_boss):
    def _boom(ch):
        raise OSError("mesh down")

    as_boss.setattr(boss, "_channel_members", _boom)
    sent = []
    as_boss.setattr(boss, "_boss_irc", lambda mt, **kw: sent.append((mt, kw)) or {"ok": True})
    with pytest.raises(SystemExit) as exc:
        boss._cmd_brief(argparse.Namespace(name="qa", task="x"))
    assert exc.value.code == 1
    assert sent == []
