"""Per-helper JSONL audit log of agent activity.

Captures one line per ``AssistantMessage`` emitted by an agent runner. Used by
the boss session for after-the-fact visibility into helper behavior — and as
the primary observability surface for backends (Codex, ACP) where the broker
cannot synchronously gate tool calls.

Design spec: docs/superpowers/specs/2026-05-28-helper-boss-permission-broker.md
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from culture.clients._perm_broker import culture_home

logger = logging.getLogger(__name__)

# Per-field size cap so a single oversized tool result / input / thinking
# block cannot bloat the log. 16 KiB is comfortable for a full Read result on
# a small file or a multi-line Bash output; large blobs are truncated and
# marked.
_FIELD_CAP_BYTES = 16 * 1024
# Legacy short preview kept alongside full content for back-compat consumers.
_PREVIEW_CHARS = 200


def _audit_dir() -> str:
    return os.path.join(culture_home(), "audit")


def audit_path_for(nick: str) -> str:
    return os.path.join(_audit_dir(), f"{nick}.jsonl")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _digest(value: Any) -> str:
    try:
        encoded = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    except TypeError:
        encoded = repr(value).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()[:16]}"


def _preview(value: Any) -> str:
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False)
        except TypeError:
            text = repr(value)
    return text[:_PREVIEW_CHARS]


def _stringify(value: Any) -> str:
    """Convert any JSON-ish value to a string. Used for size-capping."""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return repr(value)


def _cap(value: Any, cap_bytes: int = _FIELD_CAP_BYTES) -> str:
    """Cap a stringified value at ``cap_bytes`` (UTF-8). Marks truncation
    with a suffix so the dashboard can show "(truncated, N bytes total)"."""
    text = _stringify(value)
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= cap_bytes:
        return text
    head = encoded[:cap_bytes].decode("utf-8", errors="replace")
    return f"{head}\n…[truncated, {len(encoded)} bytes total]"


def _summarise_assistant_message(msg: dict[str, Any]) -> dict[str, Any]:
    """Summarize the per-turn assistant message for the audit JSONL.

    Captures everything the dashboard needs to render a session view with the
    same fidelity as a regular Claude Code session: per-block text,
    extended-thinking content, tool calls WITH inputs, and tool results
    (size-capped so a single huge output can't bloat the log). The legacy
    ``input_digest`` / ``content_digest`` / ``preview`` fields are preserved
    alongside the new ``input`` / ``content`` fields so older consumers
    continue to work.
    """
    text_chunks: list[str] = []
    thinking_chunks: list[str] = []
    tool_uses: list[dict[str, Any]] = []
    tool_results: list[dict[str, Any]] = []
    for block in msg.get("content", []) or []:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "text":
            text_value = block.get("text")
            if isinstance(text_value, str):
                text_chunks.append(text_value)
        elif block_type == "thinking":
            think_value = block.get("text") or block.get("thinking")
            if isinstance(think_value, str):
                thinking_chunks.append(think_value)
        elif block_type == "tool_use":
            input_value = block.get("input")
            tool_uses.append(
                {
                    "name": block.get("name", ""),
                    "input": _cap(input_value),
                    "input_digest": _digest(input_value),
                }
            )
        elif block_type == "tool_result":
            content = block.get("content")
            tool_results.append(
                {
                    "name": block.get("name", ""),
                    "content": _cap(content),
                    "content_digest": _digest(content),
                    "preview": _preview(content),
                }
            )
    return {
        "text": "\n".join(text_chunks),
        "thinking": "\n".join(thinking_chunks),
        "tool_uses": tool_uses,
        "tool_results": tool_results,
    }


class AuditWriter:
    """Append-only JSONL writer for a single helper's activity.

    Thread/task-safe via an internal asyncio.Lock — multiple ``write()`` calls
    on the same instance serialise to preserve line atomicity. Writes are
    fsync'd at the end of each line so a kernel crash does not lose the
    most-recent line's prefix.
    """

    def __init__(self, nick: str) -> None:
        if not nick:
            raise ValueError("AuditWriter requires a non-empty nick")
        self._nick = nick
        self._path = audit_path_for(nick)
        self._lock = asyncio.Lock()

    @property
    def path(self) -> str:
        return self._path

    async def write(self, msg: dict[str, Any]) -> None:
        """Append one JSONL line summarising an agent message.

        ``msg`` follows the dict shape produced by each backend's runner: a
        top-level ``{"type": "assistant", "model": ..., "content": [...]}``.
        Non-assistant messages are skipped to keep the log focused on agent
        actions.
        """
        if msg.get("type") != "assistant":
            return
        line = self._build_line(msg)
        async with self._lock:
            await asyncio.to_thread(self._append_line_sync, line)

    def _build_line(self, msg: dict[str, Any]) -> str:
        record = {
            "ts": _now_iso(),
            "nick": self._nick,
            "type": "assistant",
            "model": msg.get("model", ""),
            **_summarise_assistant_message(msg),
        }
        return json.dumps(record, ensure_ascii=False)

    def _append_line_sync(self, line: str) -> None:
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
        except OSError:
            logger.debug("Failed to ensure audit dir for %s", self._nick, exc_info=True)
            return
        try:
            fd = os.open(
                self._path,
                os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                0o600,
            )
        except OSError:
            logger.warning("Failed to open audit log %s", self._path, exc_info=True)
            return
        try:
            handle = os.fdopen(fd, "a", encoding="utf-8")
        except OSError:
            os.close(fd)
            logger.warning("Failed to wrap audit log fd %s", self._path, exc_info=True)
            return
        try:
            with handle:
                handle.write(line + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError:
            logger.warning("Failed to append to audit log %s", self._path, exc_info=True)
