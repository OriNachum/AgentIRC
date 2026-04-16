"""Event type catalog and render-template registry.

Event type names follow the dotted-lowercase convention enforced by
`EVENT_TYPE_RE` in `culture.constants`. Render templates map a type to a
function that produces the human-readable PRIVMSG body for humans and
vanilla IRC clients. The structured payload is attached as IRCv3 message
tags by the server's emit path (see `culture/agentirc/ircd.py`); this
module is presentation-only.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from culture.constants import EVENT_TYPE_RE

logger = logging.getLogger(__name__)

RenderFn = Callable[[dict[str, Any], str | None], str]

_TEMPLATES: dict[str, RenderFn] = {}


def register(event_type: str, fn: RenderFn) -> None:
    _TEMPLATES[event_type] = fn


def validate_event_type(name: str) -> bool:
    return bool(EVENT_TYPE_RE.match(name))


def render_event(event_type: str, data: dict[str, Any], channel: str | None) -> str:
    fn = _TEMPLATES.get(event_type)
    if fn is None:
        return f"{event_type} {data}"
    try:
        return fn(data, channel)
    except Exception:
        logger.exception("render template for %s failed", event_type)
        return f"{event_type} {data}"


# -------- built-in render templates --------


def _nick_action(verb: str) -> RenderFn:
    def _render(data, channel):
        nick = data.get("nick", "<unknown>")
        if channel:
            return f"{nick} {verb} {channel}"
        return f"{nick} {verb}"

    return _render


register("user.join", _nick_action("joined"))
register("user.part", _nick_action("left"))
register(
    "user.quit",
    lambda d, c: f"{d.get('nick', '<unknown>')} quit: {d.get('reason', '')}".rstrip(": "),
)

register("agent.connect", lambda d, c: f"{d.get('nick', '<unknown>')} connected")
register(
    "agent.disconnect",
    lambda d, c: f"{d.get('nick', '<unknown>')} disconnected",
)

register("console.open", lambda d, c: f"{d.get('nick', '<unknown>')} opened a console")
register("console.close", lambda d, c: f"{d.get('nick', '<unknown>')} closed their console")

register("server.wake", lambda d, c: f"server {d.get('server', '<unknown>')} is up")
register(
    "server.sleep",
    lambda d, c: f"server {d.get('server', '<unknown>')} is shutting down",
)
register("server.link", lambda d, c: f"linked to {d.get('peer', '<unknown>')}")
register("server.unlink", lambda d, c: f"unlinked from {d.get('peer', '<unknown>')}")

register("room.create", lambda d, c: f"{d.get('nick', '<unknown>')} created room {c}")
register("room.archive", lambda d, c: f"{d.get('nick', '<unknown>')} archived {c}")
register("room.meta", lambda d, c: f"{d.get('nick', '<unknown>')} updated {c} metadata")

register(
    "thread.create",
    lambda d, c: f"{d.get('nick', '<unknown>')} started thread [{d.get('thread', '?')}] in {c}",
)
register(
    "thread.message",
    lambda d, c: f"[{d.get('thread', '?')}] {d.get('nick', '<unknown>')}: {d.get('text', '')}",
)
register(
    "thread.close",
    lambda d, c: f"thread [{d.get('thread', '?')}] in {c} closed",
)

register(
    "tags.update",
    lambda d, c: f"{d.get('nick', '<unknown>')} tags → {', '.join(d.get('tags', []))}",
)
