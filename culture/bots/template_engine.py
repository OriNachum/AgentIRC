"""Simple dot-path template engine for bot message rendering."""

from __future__ import annotations

import json
import re

_TOKEN_RE = re.compile(r"\{(\w+(?:\.[^}]+)?)\}")


def _resolve_path(data: dict, path: str) -> str | None:
    """Walk a dot-separated path into a nested dict.

    Returns the string representation of the value, or None if any
    segment is missing.
    """
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    if current is None:
        return "null"
    return str(current)


def render_template(template: str, payload: dict | str) -> str | None:
    """Render a template string with ``{key.field.subfield}`` tokens.

    Payload keys are available directly (e.g. ``{event.nick}``) and
    via the ``body`` alias (e.g. ``{body.event.nick}``).  ``body``
    always points to the full payload for backward compatibility.

    Args:
        template: Template string with ``{key.path}`` placeholders.
        payload: The incoming payload dict.

    Returns:
        The rendered string, or None if any token could not be resolved
        (caller should fall back based on the bot's ``fallback`` config).
    """
    # body last so it always wins even if payload contains a "body" key.
    wrapper = {**(payload if isinstance(payload, dict) else {}), "body": payload}

    def _replace(match: re.Match) -> str:
        path = match.group(1)
        value = _resolve_path(wrapper, path)
        if value is None:
            raise _UnresolvedToken(path)
        return value

    try:
        return _TOKEN_RE.sub(_replace, template)
    except _UnresolvedToken:
        return None


def render_fallback(payload: dict, mode: str = "json") -> str:
    """Render a payload using the fallback mode."""
    if mode == "json":
        return json.dumps(payload, indent=None, ensure_ascii=False)
    return str(payload)


class _UnresolvedToken(Exception):
    pass
