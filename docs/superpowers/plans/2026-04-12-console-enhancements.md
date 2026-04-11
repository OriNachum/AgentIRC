# Console Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add agent status indicators in the sidebar (#218), auto-read history on channel switch (#219), and a help menu to the Culture console TUI.

**Architecture:** Three focused changes to the existing Textual console app. A new `status.py` module queries daemon IPC sockets for agent activity. The `_switch_to_channel()` method centralizes channel switching with auto-history. A `/help` command and `Ctrl+H` binding render command reference in the chat panel.

**Tech Stack:** Python 3.12+, Textual TUI framework, asyncio, Unix domain sockets (existing IPC layer)

**Spec:** `docs/superpowers/specs/2026-04-12-console-enhancements-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `culture/console/commands.py` | Modify | Add `HELP` command type |
| `culture/console/status.py` | Create | Daemon socket discovery + IPC status queries |
| `culture/console/widgets/sidebar.py` | Modify | Add `activity` field to `EntityItem`, update `_EntityRow` rendering |
| `culture/console/app.py` | Modify | Add `_switch_to_channel()`, status poll timer, help handler, `Ctrl+H` binding |
| `tests/test_console_commands.py` | Modify | Add `/help` parser test |
| `tests/test_console_status.py` | Create | Tests for status module |
| `tests/test_console_client.py` | Modify | Add auto-read integration test |

---

### Task 1: Add HELP command to parser

**Files:**
- Modify: `culture/console/commands.py:9-29` (CommandType enum)
- Modify: `culture/console/commands.py:46-63` (_COMMANDS dict)
- Test: `tests/test_console_commands.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_console_commands.py`:

```python
def test_parse_help():
    result = parse_command("/help")
    assert result.type == CommandType.HELP
    assert result.args == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_console_commands.py::test_parse_help -v`
Expected: FAIL with `AttributeError: HELP` (not in enum yet)

- [ ] **Step 3: Add HELP to CommandType enum**

In `culture/console/commands.py`, add `HELP = auto()` after `QUIT = auto()` (line 28):

```python
    QUIT = auto()
    HELP = auto()
    UNKNOWN = auto()
```

Note: `HELP` must come before `UNKNOWN` to keep `UNKNOWN` as the last value.

- [ ] **Step 4: Add help to _COMMANDS dict**

In `culture/console/commands.py`, add to the `_COMMANDS` dict (around line 62):

```python
    "quit": CommandType.QUIT,
    "help": CommandType.HELP,
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_console_commands.py -v`
Expected: All tests pass including `test_parse_help`

- [ ] **Step 6: Commit**

```bash
git add culture/console/commands.py tests/test_console_commands.py
git commit -m "feat(console): add HELP command type to parser (#218, #219)"
```

---

### Task 2: Add activity field to EntityItem and update sidebar rendering

**Files:**
- Modify: `culture/console/widgets/sidebar.py:18-34` (EntityItem dataclass)
- Modify: `culture/console/widgets/sidebar.py:93-115` (_EntityRow class)

- [ ] **Step 1: Add activity field to EntityItem**

In `culture/console/widgets/sidebar.py`, update the `EntityItem` dataclass:

```python
@dataclass
class EntityItem:
    """An entity (agent / human / bot / admin) entry in the sidebar."""

    nick: str
    entity_type: str = "agent"  # "agent" | "admin" | "human" | "bot"
    online: bool = True
    icon: str = ""
    activity: str = ""  # "working" | "idle" | "paused" | "circuit-open" | ""
```

- [ ] **Step 2: Add activity indicator mapping**

Below the existing `_TYPE_ICON` dict (after line 47), add:

```python
# Activity indicators for agent status
_ACTIVITY_INDICATOR: dict[str, str] = {
    "working": "[green]●[/]",
    "idle": "[dim]○[/]",
    "paused": "[yellow]⏸[/]",
    "circuit-open": "[red]⚠[/]",
}
```

- [ ] **Step 3: Update _EntityRow to use activity indicators**

Replace the `_EntityRow.__init__` method (lines 107-111):

```python
    def __init__(self, entity: EntityItem) -> None:
        if entity.activity and entity.activity in _ACTIVITY_INDICATOR:
            dot = _ACTIVITY_INDICATOR[entity.activity]
        elif entity.online:
            dot = "[green]●[/]"
        else:
            dot = "[dim]○[/]"
        icon = entity.icon or _TYPE_ICON.get(entity.entity_type, "")
        markup = f"{dot} {icon} {entity.nick}"
        super().__init__(markup, markup=True)
        self._nick = entity.nick
```

- [ ] **Step 4: Verify existing console tests still pass**

Run: `pytest tests/test_console_commands.py tests/test_console_client.py -v`
Expected: All pass (sidebar changes are rendering-only, no test breakage)

- [ ] **Step 5: Commit**

```bash
git add culture/console/widgets/sidebar.py
git commit -m "feat(console): add activity status indicators to sidebar entities (#218)"
```

---

### Task 3: Create status polling module

**Files:**
- Create: `culture/console/status.py`
- Create: `tests/test_console_status.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_console_status.py`:

```python
"""Tests for console status polling module."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from culture.console.status import discover_agent_sockets, query_all_agents


def test_discover_no_sockets(tmp_path):
    """discover_agent_sockets returns empty list when no sockets exist."""
    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(tmp_path)}):
        result = discover_agent_sockets()
    assert result == []


def test_discover_finds_sockets(tmp_path):
    """discover_agent_sockets finds culture-*.sock files."""
    sock1 = tmp_path / "culture-spark-claude.sock"
    sock1.touch()
    sock2 = tmp_path / "culture-spark-daria.sock"
    sock2.touch()
    # Non-matching file should be ignored
    (tmp_path / "other.sock").touch()

    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(tmp_path)}):
        result = discover_agent_sockets()

    nicks = [nick for nick, _ in result]
    assert sorted(nicks) == ["spark-claude", "spark-daria"]


@pytest.mark.asyncio
async def test_query_all_agents_no_sockets(tmp_path):
    """query_all_agents returns empty dict when no sockets exist."""
    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(tmp_path)}):
        result = await query_all_agents()
    assert result == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_console_status.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'culture.console.status'`

- [ ] **Step 3: Implement status module**

Create `culture/console/status.py`:

```python
"""Lightweight daemon IPC status queries for the console."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def discover_agent_sockets() -> list[tuple[str, Path]]:
    """List culture daemon sockets in $XDG_RUNTIME_DIR.

    Returns a list of ``(nick, socket_path)`` tuples.
    """
    runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
    results: list[tuple[str, Path]] = []
    if not runtime_dir.is_dir():
        return results
    for entry in runtime_dir.iterdir():
        if entry.name.startswith("culture-") and entry.name.endswith(".sock"):
            nick = entry.name[len("culture-") : -len(".sock")]
            results.append((nick, entry))
    return results


async def query_agent_status(socket_path: Path) -> dict:
    """Query a single daemon socket for status (no LLM query).

    Returns a dict with ``activity``, ``paused``, ``circuit_open``,
    ``running`` keys, or an empty dict on failure.
    """
    from culture.cli.shared.ipc import ipc_request

    resp = await ipc_request(str(socket_path), "status")
    if resp is None or not resp.get("ok"):
        return {}
    return resp.get("data", {})


def _derive_activity(data: dict) -> str:
    """Derive a single activity string from daemon status fields."""
    if data.get("circuit_open"):
        return "circuit-open"
    if data.get("paused"):
        return "paused"
    return data.get("activity", "idle")


async def query_all_agents() -> dict[str, str]:
    """Query all local daemon sockets and return nick -> activity mapping."""
    import asyncio

    sockets = discover_agent_sockets()
    if not sockets:
        return {}

    results: dict[str, str] = {}

    async def _query_one(nick: str, path: Path) -> None:
        try:
            data = await asyncio.wait_for(query_agent_status(path), timeout=3.0)
            if data:
                results[nick] = _derive_activity(data)
        except (TimeoutError, Exception):
            logger.debug("Failed to query status for %s", nick)

    await asyncio.gather(*[_query_one(nick, path) for nick, path in sockets])
    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_console_status.py -v`
Expected: All 3 tests pass

- [ ] **Step 5: Commit**

```bash
git add culture/console/status.py tests/test_console_status.py
git commit -m "feat(console): add status polling module for daemon IPC queries (#218)"
```

---

### Task 4: Add status polling timer to ConsoleApp

**Files:**
- Modify: `culture/console/app.py:1-24` (imports)
- Modify: `culture/console/app.py:56-67` (__init__)
- Modify: `culture/console/app.py:105-111` (on_mount)
- Modify: `culture/console/app.py:442-474` (_show_agents)
- Modify: `culture/console/app.py:524-537` (action_quit_app)

- [ ] **Step 1: Add import for status module**

In `culture/console/app.py`, add after the existing console imports (line 20):

```python
from culture.console.status import query_all_agents
```

Also add a constant after `BUFFER_INTERVAL` (line 24):

```python
BUFFER_INTERVAL = 10.0  # seconds between UI refreshes
STATUS_POLL_INTERVAL = 30.0  # seconds between agent status polls
```

- [ ] **Step 2: Add status poll task to __init__**

In `ConsoleApp.__init__`, add after `self._background_tasks` (line 67):

```python
        self._background_tasks: set[asyncio.Task] = set()
        self._status_poll_task: asyncio.Task | None = None
```

- [ ] **Step 3: Start status poll in on_mount**

In `on_mount`, add after the buffer task creation (line 108):

```python
    def on_mount(self) -> None:
        """Set sub-title and kick off the buffer-drain loop."""
        self.sub_title = f"{self._client.nick}@{self._server_name}"
        self._buffer_task = asyncio.create_task(self._buffer_loop())
        self._status_poll_task = asyncio.create_task(self._status_poll_loop())

        # Populate sidebar with any channels already joined at startup
        self._sync_sidebar()
```

- [ ] **Step 4: Implement the status poll loop**

Add after `_flush_messages` (after line 141), before the Input handler section:

```python
    async def _status_poll_loop(self) -> None:
        """Periodically poll agent daemon sockets for status updates."""
        # Initial poll on startup
        await self._poll_agent_status()
        while True:
            try:
                await asyncio.sleep(STATUS_POLL_INTERVAL)
                await self._poll_agent_status()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Error in _status_poll_loop")

    async def _poll_agent_status(self) -> None:
        """Query daemon sockets and update sidebar entity activity."""
        status_map = await query_all_agents()
        if not status_map:
            return
        sidebar: Sidebar = self.query_one(Sidebar)
        updated = False
        new_entities = []
        for ent in sidebar.entities:
            if ent.nick in status_map:
                new_ent = EntityItem(
                    nick=ent.nick,
                    entity_type=ent.entity_type,
                    online=ent.online,
                    icon=ent.icon,
                    activity=status_map[ent.nick],
                )
                new_entities.append(new_ent)
                updated = True
            else:
                new_entities.append(ent)
        if updated:
            sidebar.entities = new_entities
```

- [ ] **Step 5: Update _show_agents to include activity**

In `_show_agents` (line 471-473), update entity creation to preserve activity from status polling:

```python
        # Update sidebar entity roster
        status_map = await query_all_agents()
        entity_items = [
            EntityItem(
                nick=nick,
                entity_type="agent",
                online=True,
                activity=status_map.get(nick, ""),
            )
            for nick in sorted(all_agents)
        ]
        sidebar.entities = entity_items
```

- [ ] **Step 6: Cancel status poll in quit**

In `action_quit_app`, add cancellation for the status poll task. Replace the method (lines 524-537):

```python
    async def action_quit_app(self) -> None:
        """Disconnect the IRC client and exit the app."""
        for task_ref in (self._buffer_task, self._status_poll_task):
            if task_ref:
                task_ref.cancel()
        tasks_to_cancel = [
            t for t in (self._buffer_task, self._status_poll_task) if t
        ]
        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
        self._buffer_task = None
        self._status_poll_task = None

        if self._client.connected:
            try:
                await self._client.disconnect()
            except Exception:
                logger.exception("Error disconnecting IRC client during quit")

        self.exit()
```

- [ ] **Step 7: Run all console tests**

Run: `pytest tests/test_console_commands.py tests/test_console_client.py tests/test_console_status.py -v`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
git add culture/console/app.py
git commit -m "feat(console): add 30s status polling timer for sidebar updates (#218)"
```

---

### Task 5: Implement auto-read on channel switch

**Files:**
- Modify: `culture/console/app.py:185-209` (_handle_join, _handle_part)
- Modify: `culture/console/app.py:495-518` (channel cycling)
- Modify: `culture/console/app.py:543-557` (sidebar channel selected)

- [ ] **Step 1: Add _switch_to_channel method**

Add a new method in the "Internal helpers" section (after `_sync_sidebar`, around line 578):

```python
    async def _switch_to_channel(self, channel: str) -> None:
        """Switch to a channel, update UI, and auto-load recent history."""
        if not channel:
            return
        # Guard against stale results from rapid switching
        self._current_channel = channel
        self._current_view = "chat"

        sidebar: Sidebar = self.query_one(Sidebar)
        chat: ChatPanel = self.query_one(ChatPanel)
        sidebar.active_channel = channel
        chat.set_channel(channel)
        chat.clear_log()

        # Re-show input if hidden (e.g., coming from overview/status view)
        try:
            input_widget = self.query_one(self._CHAT_INPUT_ID)
            input_widget.display = True
        except Exception:
            pass

        # Fetch recent history
        entries = await self._client.history(channel, limit=20)
        # Stale check: if user switched away during fetch, discard results
        if self._current_channel != channel:
            return
        for e in entries:
            try:
                ts = float(e.get("timestamp", 0))
            except (ValueError, TypeError):
                ts = time.time()
            chat.add_message(ts, "", e.get("nick", ""), e.get("text", ""))
        if not entries:
            chat.add_message(
                time.time(), "", "system", f"[dim]No history for {channel}[/]"
            )
```

- [ ] **Step 2: Update _handle_join to use _switch_to_channel**

Replace `_handle_join` (lines 185-195):

```python
    async def _handle_join(self, cmd) -> None:  # noqa: ANN001
        chat: ChatPanel = self.query_one(ChatPanel)
        if not cmd.args:
            chat.add_message(time.time(), "", "system", "[red]Usage: /join #channel[/]")
            return
        channel = cmd.args[0]
        await self._client.join(channel)
        self._sync_sidebar()
        chat.add_message(time.time(), "", "system", f"Joined [bold]{channel}[/]")
        await self._switch_to_channel(channel)
```

- [ ] **Step 3: Update _cycle_channel to spawn async switch**

Replace `_cycle_channel` and the action methods (lines 495-518):

```python
    def action_next_channel(self) -> None:
        """Switch to the next channel in the list."""
        self._cycle_channel(+1)

    def action_prev_channel(self) -> None:
        """Switch to the previous channel in the list."""
        self._cycle_channel(-1)

    def _cycle_channel(self, direction: int) -> None:
        """Cycle through joined channels by direction (+1 or -1)."""
        channels = sorted(self._client.joined_channels)
        if not channels:
            return
        if self._current_channel not in channels:
            target = channels[0]
        else:
            idx = channels.index(self._current_channel)
            idx = (idx + direction) % len(channels)
            target = channels[idx]

        task = asyncio.create_task(self._switch_to_channel(target))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
```

- [ ] **Step 4: Update on_sidebar_channel_selected**

Replace `on_sidebar_channel_selected` (lines 543-557):

```python
    def on_sidebar_channel_selected(self, event: Sidebar.ChannelSelected) -> None:
        """Switch to the selected channel when user clicks sidebar."""
        task = asyncio.create_task(self._switch_to_channel(event.channel))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
```

- [ ] **Step 5: Run all console tests**

Run: `pytest tests/test_console_commands.py tests/test_console_client.py tests/test_console_status.py -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add culture/console/app.py
git commit -m "feat(console): auto-read channel history on switch (#219)"
```

---

### Task 6: Implement help menu

**Files:**
- Modify: `culture/console/app.py:33-39` (BINDINGS)
- Modify: `culture/console/app.py:70-87` (command_handlers dict)
- Add handler method in app.py

- [ ] **Step 1: Add Ctrl+H binding**

In `ConsoleApp.BINDINGS` (lines 33-39), add the help binding:

```python
    BINDINGS = [
        Binding("ctrl+o", "show_overview", "Overview", show=True),
        Binding("ctrl+s", "show_status", "Status", show=True),
        Binding("ctrl+h", "show_help", "Help", show=True),
        Binding("escape", "back_to_chat", "Chat", show=True),
        Binding("ctrl+q", "quit_app", "Quit", show=True),
        Binding("tab", "next_channel", "Next channel", show=False),
        Binding("shift+tab", "prev_channel", "Prev channel", show=False),
    ]
```

- [ ] **Step 2: Register HELP in dispatch table**

In `_command_handlers` dict (around line 86), add:

```python
            CommandType.SERVER: self._handle_server,
            CommandType.QUIT: self._handle_quit,
            CommandType.HELP: self._handle_help,
```

- [ ] **Step 3: Implement help handler and action**

Add after `_handle_quit` (around line 342):

```python
    def _handle_help(self, cmd) -> None:  # noqa: ANN001
        self.action_show_help()

    def action_show_help(self) -> None:
        """Show help content with all commands and keybindings."""
        chat: ChatPanel = self.query_one(ChatPanel)
        lines = [
            "[bold $warning]COMMANDS[/]",
            "",
            "  [bold]/help[/]                  Show this help",
            "  [bold]/join[/] #channel         Join a channel",
            "  [bold]/part[/] [#channel]       Leave a channel",
            "  [bold]/read[/] [#ch] [-n N]     Read channel history (default 50)",
            "  [bold]/who[/] [target]          List channel members",
            "  [bold]/send[/] <target> <text>  Send a direct message",
            "  [bold]/channels[/]              List server channels",
            "  [bold]/agents[/]                List visible agents",
            "  [bold]/status[/] [agent]        Show status info",
            "  [bold]/overview[/]              Show mesh overview",
            "  [bold]/icon[/] <emoji>          Set your icon",
            "  [bold]/topic[/] #ch <text>      Set channel topic",
            "  [bold]/kick[/] #ch <nick>       Kick a user",
            "  [bold]/invite[/] <nick> #ch     Invite a user",
            "  [bold]/server[/] [name]         Switch server (restarts console)",
            "  [bold]/quit[/]                  Exit console",
            "",
            "[bold $warning]KEYBINDINGS[/]",
            "",
            "  [bold]Tab / Shift+Tab[/]        Cycle channels",
            "  [bold]Ctrl+O[/]                 Overview",
            "  [bold]Ctrl+S[/]                 Status",
            "  [bold]Ctrl+H[/]                 Help",
            "  [bold]Escape[/]                 Back to chat",
            "  [bold]Ctrl+Q[/]                 Quit",
        ]
        chat.set_content("Help", lines)

        # Hide input — not meaningful in help view
        try:
            input_widget = self.query_one(self._CHAT_INPUT_ID)
            input_widget.display = False
        except Exception:
            pass
```

- [ ] **Step 4: Run all console tests**

Run: `pytest tests/test_console_commands.py tests/test_console_client.py tests/test_console_status.py -v`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add culture/console/app.py
git commit -m "feat(console): add /help command and Ctrl+H binding"
```

---

### Task 7: Manual verification and final cleanup

- [ ] **Step 1: Start a server and agent**

```bash
culture server start
culture start spark-claude
```

(If no server/agent available, skip to step 4 for test-only verification.)

- [ ] **Step 2: Launch console and test all features**

```bash
culture console
```

Verify:
1. Sidebar shows agent status indicators (green dot for working agents)
2. Switch channels with Tab — history auto-loads (20 messages)
3. Click a channel in sidebar — same auto-load behavior
4. `/join #test` — joins and auto-loads history
5. `/help` shows command reference
6. `Ctrl+H` shows same help
7. `Escape` returns to chat
8. `/read -n 50` still works with custom limit
9. Wait 30s — status indicators update

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/test_console_commands.py tests/test_console_client.py tests/test_console_status.py tests/test_console_integration.py tests/test_console_connection.py -v`
Expected: All pass

- [ ] **Step 4: Run full project tests**

Run: `pytest -n auto`
Expected: No regressions

- [ ] **Step 5: Create follow-up issue for room→channel rename**

```bash
gh issue create --title "Rename room/rooms to channel/channels across codebase" --body "Follow-up from #218/#219 console enhancements.

The codebase still uses 'room' terminology in several places that should be 'channel':
- \`culture/protocol/extensions/rooms.md\` — protocol extension
- \`culture/protocol/extensions/tags.md\` — references rooms
- \`culture/protocol/extensions/federation.md\` — references rooms
- \`culture/overview/model.py\` — \`Room\` class
- \`culture/overview/renderer_text.py\` — references \`Room\`
- \`culture/learn_prompt.py\` — references rooms

Scope: rename \`Room\` → \`Channel\` in code and \`room\`/\`rooms\` → \`channel\`/\`channels\` in docs."
```
