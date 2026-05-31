"""Channel seed-text persistence (v8.19.18).

A "seed" is the initial brief / topic the boss attaches to a task
channel when opening it. Once persisted it stays — subsequent briefs
don't overwrite. Surfaced in the dashboard as a collapsible "Seed
brief" header so the operator can see the original mission without
scrolling back through chat.

This is the channel-level analog of the boss-level mission
persistence in ``culture/clients/_mission.py``: brief→file capture
plus read API, but channel-keyed instead of nick-keyed and
write-once instead of rotating.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from culture.clients._perm_broker import seed_path_for

logger = logging.getLogger(__name__)


def persist_seed(channel: str, text: str, *, overwrite: bool = False) -> bool:
    """Write the seed for ``channel``. Returns True iff a write happened.

    Idempotent by default — if a seed file already exists, the new text
    is NOT written. Pass ``overwrite=True`` to replace (e.g. when an
    explicit ``--topic`` is rewriting the topic at spawn time).

    The file format is two lines of header (timestamp + channel) plus
    a blank line, then the seed body — readable by humans, parseable
    by ``load_seed``.
    """
    text = (text or "").strip()
    if not text:
        return False
    try:
        path = seed_path_for(channel)
    except ValueError as exc:
        logger.warning("seed write skipped: %s", exc)
        return False
    if os.path.exists(path) and not overwrite:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    body = f"<!-- seed for {channel} written {ts} -->\n\n{text}\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return True


def load_seed(channel: str) -> dict[str, str] | None:
    """Read the seed for ``channel``. Returns dict or None.

    Returned dict shape:
        {"channel": "#name", "text": "the brief", "ts": "2026-05-31T..."}
    """
    try:
        path = seed_path_for(channel)
    except ValueError:
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError:
        return None
    ts = ""
    lines = raw.splitlines()
    if lines and lines[0].startswith("<!-- seed for"):
        # Extract the timestamp from the header comment.
        head = lines[0]
        marker = "written "
        idx = head.find(marker)
        if idx >= 0:
            tail = head[idx + len(marker) :].rstrip("-> ").strip()
            ts = tail
        # Body starts after the header + (usually) one blank line.
        body = "\n".join(lines[1:]).lstrip("\n")
    else:
        body = raw
    return {"channel": channel, "text": body.strip(), "ts": ts}


def clear_seed(channel: str) -> bool:
    """Remove the persisted seed. Returns True iff a file was deleted."""
    try:
        path = seed_path_for(channel)
    except ValueError:
        return False
    try:
        os.remove(path)
        return True
    except OSError:
        return False
