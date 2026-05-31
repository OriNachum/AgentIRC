"""Living per-channel brief (v8.19.24) — the onboarding doc.

The v8.19.18 ``_seed`` is *write-once initial*: the seed brief is the
mission as the boss saw it when opening the channel. It never updates.

This module is the *living* sibling: an append-only running log of
"what's true about this channel right now" — decisions, completed
work, current state, recent gotchas. When a new worker spawns into
the channel, the harness injects this brief into the SDK system
prompt so the worker boots with context — like a new teammate
reading the team's running notes, not just the chat log.

Trigger for the design: the user observed that a new mesh worker only
sees the IRC HISTORY (last N messages) on join. A real team onboards
new joiners with a current-state doc; the mesh should too.

Format: simple Markdown at ``~/.culture/briefs/<channel-without-hash>.md``.
First line is a level-1 heading; the rest is free-form. The harness
caps reads at 64 KiB so a runaway brief can't break a worker's context
window.

API:
    persist_section(channel, section_title, body)
        Append a dated section. Idempotent on identical body within
        the same minute (defensive against double-fires from the
        same brief).
    load_brief(channel)
        Return the full markdown (or "" if missing). Capped at
        ``READ_CAP_BYTES`` so a malicious or runaway file can't
        blow up a worker boot.
    clear_brief(channel)
        For test cleanup.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone

from culture.clients._perm_broker import culture_home

logger = logging.getLogger(__name__)

# Cap how much we read into a worker's system prompt. 64 KiB is plenty
# for a project README's worth of context but small enough that even an
# adversarial brief can't blow the context window.
READ_CAP_BYTES = 64 * 1024


def _briefs_dir() -> str:
    return os.path.join(culture_home(), "briefs")


def brief_path_for(channel: str) -> str:
    """Per-channel brief path. Channel may carry a leading ``#``; stripped.

    Channel names are validated against a safe-filename regex so the
    path stays inside ``~/.culture/briefs/`` — no traversal possible.
    """
    name = channel.lstrip("#")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError(f"invalid channel name for brief path: {channel!r}")
    return os.path.join(_briefs_dir(), f"{name}.md")


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def persist_section(channel: str, section_title: str, body: str) -> bool:
    """Append a timestamped Markdown section to the channel brief.

    Returns True iff a write happened. Returns False on:
      * empty body (trimmed),
      * invalid channel name (path-traversal guard),
      * idempotence hit: the exact same body landed in the file within
        the same minute (defends against duplicate brief fires).

    Each new section gets a ``## YYYY-MM-DD HH:MMZ — <title>`` header
    so the file is human-readable AND machine-grep-able.
    """
    body = (body or "").strip()
    if not body:
        return False
    try:
        path = brief_path_for(channel)
    except ValueError as exc:
        logger.warning("channel brief write skipped: %s", exc)
        return False
    section_title = (section_title or "update").strip() or "update"
    ts = datetime.now(tz=timezone.utc)
    header = f"## {ts.strftime('%Y-%m-%d %H:%MZ')} — {section_title}"
    new_section = f"\n\n{header}\n\n{body}\n"

    # Idempotence: if the file already ends with this exact body
    # within the last minute window (same MM stamp), don't re-write.
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                existing = fh.read()
            if header in existing.splitlines()[-30:] and body in existing[-len(body) - 1024 :]:
                return False
        except OSError:
            pass  # fall through to write

    os.makedirs(os.path.dirname(path), exist_ok=True)
    is_new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as fh:
        if is_new:
            fh.write(
                f"# Channel brief — {channel}\n\nLiving onboarding doc. Appended on every brief/decision.\n"
            )
        fh.write(new_section)
    return True


def load_brief(channel: str) -> str:
    """Return the full brief text (capped). Empty string on missing/bad path."""
    try:
        path = brief_path_for(channel)
    except ValueError:
        return ""
    try:
        size = os.path.getsize(path)
        if size > READ_CAP_BYTES:
            # Read the TAIL — last READ_CAP_BYTES bytes. A worker booting
            # against a multi-megabyte brief needs the recent state, not
            # the early history.
            with open(path, "rb") as fh:
                fh.seek(size - READ_CAP_BYTES)
                raw = fh.read()
                # Drop the partial leading line so the worker doesn't see
                # half a sentence.
                _, _, tail = raw.decode("utf-8", "replace").partition("\n")
                return f"# Channel brief — {channel}\n\n[...older history truncated...]\n{tail}"
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def has_brief(channel: str) -> bool:
    """Cheap existence check — used by the daemon to decide whether to inject."""
    try:
        path = brief_path_for(channel)
    except ValueError:
        return False
    return os.path.exists(path)


def clear_brief(channel: str) -> bool:
    """Remove the brief file. Returns True iff a file was deleted."""
    try:
        os.remove(brief_path_for(channel))
        return True
    except (OSError, ValueError):
        return False


def system_prompt_extension(channel: str) -> str:
    """Render the channel brief as a system-prompt insert for a new worker.

    Wraps the brief in a clear "you are joining mid-project" framing
    so the worker treats it as context, not as a current instruction.
    Returns "" when there's no brief — caller decides whether to
    append a no-op or skip the field entirely.
    """
    brief = load_brief(channel)
    if not brief.strip():
        return ""
    return (
        f"\n\n# Joining channel {channel} — current state\n\n"
        f"You are joining an in-flight Channel. Below is the living\n"
        f"brief other members of this Channel have been building.\n"
        f"Read it before you act so you don't repeat work or break\n"
        f"decisions that have already been made.\n\n"
        f"---\n\n"
        f"{brief}\n\n"
        f"---\n\n"
        f"End of channel brief. Your task brief follows separately.\n"
    )
