"""JSON disk persistence for conversation threads."""

from __future__ import annotations

import json
import re
from pathlib import Path


class ThreadStore:
    """Save and load thread data to/from disk as JSON files."""

    def __init__(self, data_dir: str):
        self._threads_dir = Path(data_dir) / "threads"
        self._threads_dir.mkdir(parents=True, exist_ok=True)

    def _safe_key(self, channel: str, name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9\-]", "_", f"{channel}_{name}")
        return safe

    def save(self, thread_data: dict) -> None:
        """Persist a thread's data to disk."""
        key = self._safe_key(thread_data["channel"], thread_data["name"])
        path = self._threads_dir / f"{key}.json"
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(thread_data, f, indent=2)
        tmp.rename(path)

    def delete(self, channel: str, name: str) -> None:
        """Remove a thread's persisted data."""
        key = self._safe_key(channel, name)
        path = self._threads_dir / f"{key}.json"
        if path.exists():
            path.unlink()

    def load_all(self) -> list[dict]:
        """Load all persisted threads from disk."""
        threads = []
        if not self._threads_dir.exists():
            return threads
        for path in sorted(self._threads_dir.glob("*.json")):
            try:
                with open(path) as f:
                    threads.append(json.load(f))
            except (json.JSONDecodeError, OSError) as exc:
                import logging

                logging.getLogger(__name__).warning(
                    "Skipping corrupt thread file %s: %s", path, exc
                )
        return threads
