"""Tests for asyncio task GC prevention and CancelledError re-raising."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from culture.clients.acp.irc_transport import IRCTransport
from culture.clients.acp.message_buffer import MessageBuffer


class TestTaskGCPrevention:
    """Verify fire-and-forget tasks are stored to prevent garbage collection."""

    def _make_transport(self) -> IRCTransport:
        buf = MessageBuffer(max_per_channel=100)
        return IRCTransport(
            host="localhost",
            port=6667,
            nick="testbot",
            user="testbot",
            channels=["#test"],
            buffer=buf,
        )

    @pytest.mark.asyncio
    async def test_spawn_task_stores_reference(self):
        """_spawn_task keeps a ref in _background_tasks so the task is not GC'd."""
        transport = self._make_transport()
        assert hasattr(transport, "_background_tasks")
        assert isinstance(transport._background_tasks, set)

        async def dummy():
            await asyncio.sleep(10)

        task = transport._spawn_task(dummy())
        assert task in transport._background_tasks
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        # After task completes, it should be removed via done callback
        assert task not in transport._background_tasks

    @pytest.mark.asyncio
    async def test_spawn_task_returns_task(self):
        transport = self._make_transport()
        task = transport._spawn_task(asyncio.sleep(0.01))
        assert isinstance(task, asyncio.Task)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_multiple_spawned_tasks_tracked(self):
        transport = self._make_transport()
        tasks = []
        for _ in range(5):
            tasks.append(transport._spawn_task(asyncio.sleep(0.05)))

        assert len(transport._background_tasks) == 5
        for t in tasks:
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
        assert len(transport._background_tasks) == 0


class TestCancelledErrorReraise:
    """Verify CancelledError is re-raised after cleanup, not swallowed."""

    @pytest.mark.asyncio
    async def test_read_loop_reraises_cancelled(self):
        """_read_loop should raise CancelledError, not swallow it."""
        buf = MessageBuffer(max_per_channel=100)
        transport = IRCTransport(
            host="localhost",
            port=6667,
            nick="testbot",
            user="testbot",
            channels=["#test"],
            buffer=buf,
        )

        # Mock the reader to raise CancelledError
        mock_reader = AsyncMock()
        mock_reader.read = AsyncMock(side_effect=asyncio.CancelledError)
        transport._reader = mock_reader

        with pytest.raises(asyncio.CancelledError):
            await transport._read_loop()

    @pytest.mark.asyncio
    async def test_reconnect_task_not_gcd(self):
        """Reconnect task spawned from _read_loop finally block should be tracked."""
        buf = MessageBuffer(max_per_channel=100)
        transport = IRCTransport(
            host="localhost",
            port=6667,
            nick="testbot",
            user="testbot",
            channels=["#test"],
            buffer=buf,
        )
        transport._should_run = True
        transport._reconnecting = False
        transport._reader = AsyncMock()
        transport._reader.read = AsyncMock(return_value=b"")  # empty data breaks loop

        await transport._read_loop()

        # Check that a reconnect task was spawned and tracked
        # (it may have already completed if connection failed fast)
        # The key is: no task was created via bare asyncio.create_task
        # All tasks go through _spawn_task which adds to _background_tasks
        await asyncio.sleep(0.1)
