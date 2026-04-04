"""Shared mixin for background task management across daemon variants."""

from __future__ import annotations

import asyncio


class BackgroundTaskMixin:
    """Provides fire-and-forget task spawning with GC protection.

    Callers must mix this into a class that uses asyncio event loops.
    """

    def _init_background_tasks(self) -> None:
        self._background_tasks: set[asyncio.Task] = set()

    def _spawn_task(self, coro) -> asyncio.Task:
        """Fire-and-forget create_task that keeps a ref to prevent GC."""
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task
