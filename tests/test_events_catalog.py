"""Event type validation and render-template registry."""

import pytest

from culture.agentirc.events import (
    render_event,
    validate_event_type,
)


@pytest.mark.parametrize(
    "name",
    [
        "user.join",
        "agent.connect",
        "server.link",
        "welcome-bot.greeted",
        "a.b",
        "triage-bot.classified",
    ],
)
def test_valid_types(name):
    assert validate_event_type(name) is True


@pytest.mark.parametrize(
    "name",
    [
        "",
        "nodots",
        "UPPERCASE.bad",
        ".leadingdot",
        "trailing.",
        "double..dot",
        "space in.name",
        "!.x",
    ],
)
def test_invalid_types(name):
    assert validate_event_type(name) is False


def test_render_builtin_user_join():
    body = render_event("user.join", {"nick": "ori"}, channel="#general")
    assert body == "ori joined #general"


def test_render_builtin_agent_connect():
    body = render_event("agent.connect", {"nick": "spark-claude"}, channel="#system")
    assert body == "spark-claude connected"


def test_render_unknown_type_falls_back():
    body = render_event("unknown.thing", {"k": "v"}, channel="#x")
    # Fallback should include the type name and the data dict.
    assert "unknown.thing" in body
    assert "k" in body
    assert "v" in body


def test_render_template_crash_falls_back(monkeypatch):
    from culture.agentirc import events as mod

    def boom(data, channel):
        raise RuntimeError("render broken")

    monkeypatch.setitem(mod._TEMPLATES, "user.join", boom)
    body = render_event("user.join", {"nick": "ori"}, channel="#x")
    # Render failure falls back to raw shape, not an exception.
    assert "user.join" in body
