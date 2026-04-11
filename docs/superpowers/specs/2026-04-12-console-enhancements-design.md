# Console Enhancements Design

**Date:** 2026-04-12
**Issues:** #218 (agent status), #219 (auto-read on channel switch), help menu
**Scope:** Three console TUI improvements in one PR

## Context

The Culture console (`culture/console/`) is a Textual TUI for monitoring and
interacting with the agent mesh. Two usability gaps exist:

1. **No agent status visibility** — users can't tell at a glance whether agents
   are busy, idle, paused, or in a crash loop. The daemon already tracks this
   via IPC, but the console doesn't surface it.
2. **Manual history load** — switching channels (Tab, sidebar click, /join)
   shows a blank chat until the user manually runs `/read`. History should load
   automatically.

Additionally, there is no discoverable help for available commands and
keybindings.

## Feature 1: Agent Status in Sidebar (#218)

### Data Model

Add an `activity` field to `EntityItem` in `widgets/sidebar.py`:

```python
@dataclass
class EntityItem:
    nick: str
    entity_type: str = "agent"
    online: bool = True
    icon: str = ""
    activity: str = ""  # "working" | "idle" | "paused" | "circuit-open" | ""
```

Empty string means unknown (no daemon socket found — console user, remote
entity, etc.).

### Status Module

New file `culture/console/status.py` with three functions:

- `discover_agent_sockets() -> list[tuple[str, Path]]` — lists
  `$XDG_RUNTIME_DIR/culture-*.sock` files, returns `(nick, path)` pairs.
- `query_agent_status(socket_path: Path) -> dict` — sends IPC `status`
  request (no `query=true`), returns `{activity, paused, circuit_open,
  running}`. Returns empty dict on timeout (3s) or error.
- `query_all_agents() -> dict[str, str]` — calls the above, returns
  `nick -> activity` mapping. Activity is derived from daemon fields:
  `circuit_open` -> `"circuit-open"`, `paused` -> `"paused"`,
  `running` and activity field from daemon, else `"idle"`.

Uses `culture.cli.shared.ipc.ipc_request` for socket communication — no new
IPC code needed.

### Polling Timer

`ConsoleApp` adds a `_status_poll_task` (30-second interval) alongside the
existing `_buffer_loop` (10s). On each tick:

1. Call `query_all_agents()` in a thread executor (avoids blocking the event
   loop on socket I/O).
2. Merge activity values into the current entity list.
3. Set `sidebar.entities` to trigger recompose.

The poll also runs once on mount (after initial sidebar sync).

### Sidebar Rendering

`_EntityRow.__init__` maps activity to indicator:

| Activity | Symbol | Color |
|----------|--------|-------|
| `working` | `●` | green |
| `idle` | `○` | dim |
| `paused` | `⏸` | yellow |
| `circuit-open` | `⚠` | red |
| `""` (unknown) | `●` | default (neutral) |

Format: `{indicator} {icon} {nick}`

## Feature 2: Auto-read on Channel Switch (#219)

### Core Method

Extract `_switch_to_channel(channel: str)` in `app.py`:

1. Set `self._current_channel = channel`
2. Set `self._current_view = "chat"`
3. Update `sidebar.active_channel`
4. Update `chat.set_channel(channel)`
5. Clear chat log
6. Fetch `await self._client.history(channel, limit=20)`
7. Populate chat with entries (or system message if empty)
8. Re-show input widget if hidden

### Call Sites

Replace inline channel-switching logic in:

- **`_cycle_channel(direction)`** — currently sync. Change to spawn an async
  task (`asyncio.create_task(self._switch_to_channel(...))`), same pattern as
  `on_sidebar_entity_selected`.
- **`on_sidebar_channel_selected(event)`** — replace body with
  `create_task(self._switch_to_channel(event.channel))`.
- **`_handle_join(cmd)`** — after `await self._client.join(channel)`, call
  `await self._switch_to_channel(channel)`. Keep the "Joined" system message.

### Rapid Switching Guard

When the user tabs rapidly through channels, multiple history fetches may be
in flight. `_switch_to_channel` should check that `self._current_channel`
still matches the requested channel before populating the chat. If the user
has already moved on, discard the stale results silently.

### Manual /read

Unchanged — `/read [#channel] [-n N]` still works for custom limits. It
overrides the auto-loaded 20 messages.

## Feature 3: Help Menu

### Parser

Add `HELP = auto()` to `CommandType` enum in `commands.py`.
Add `"help": CommandType.HELP` to `_COMMANDS` dict.

### Binding

Add `Binding("ctrl+h", "show_help", "Help", show=True)` to
`ConsoleApp.BINDINGS`.

### Handler

`_handle_help()` and `action_show_help()` render help content via
`chat.set_content("Help", lines)`:

```
COMMANDS
  /help              Show this help
  /join #channel     Join a channel
  /part [#channel]   Leave a channel
  /read [#ch] [-n N] Read channel history (default 50)
  /who [target]      List channel members
  /send <target> <text> Send a direct message
  /channels          List server channels
  /agents            List visible agents
  /status [agent]    Show status info
  /overview          Show mesh overview
  /icon <emoji>      Set your icon
  /topic #ch <text>  Set channel topic
  /kick #ch <nick>   Kick a user
  /invite <nick> #ch Invite a user
  /server [name]     Switch server (restarts console)
  /quit              Exit console

KEYBINDINGS
  Tab / Shift+Tab    Cycle channels
  Ctrl+O             Overview
  Ctrl+S             Status
  Ctrl+H             Help
  Escape             Back to chat
  Ctrl+Q             Quit
```

## Files Modified

| File | Change |
|------|--------|
| `culture/console/widgets/sidebar.py` | Add `activity` field to `EntityItem`, update `_EntityRow` rendering |
| `culture/console/app.py` | Add `_switch_to_channel()`, status poll timer, help handler, `Ctrl+H` binding |
| `culture/console/commands.py` | Add `HELP` to `CommandType` and `_COMMANDS` |
| `culture/console/status.py` | **New** — lightweight daemon IPC status queries |

## Testing

### Automated

- **Unit test**: `test_console_commands.py` — add test for `/help` parsing.
- **Integration test**: `test_console_client.py` — verify history fetch on
  channel switch returns expected messages.
- **Status module test**: New `test_console_status.py` — test
  `discover_agent_sockets` with a temp socket, `query_agent_status` against
  a running daemon.

### Manual Verification

1. Start a server and at least one agent: `culture server start && culture start spark-claude`
2. Launch console: `culture console`
3. Verify sidebar shows agent status indicators (busy/idle)
4. Switch channels with Tab — confirm history auto-loads (20 messages)
5. Click a channel in sidebar — same auto-load behavior
6. Type `/help` or press Ctrl+H — confirm help renders
7. Type `/read -n 50` — confirm manual read still works with custom limit
8. Wait 30s — verify sidebar status indicators update

## Follow-up

- **room→channel rename**: Protocol extensions (`rooms.md`, `tags.md`,
  `federation.md`), overview model (`Room` class), and associated docs still
  use "room" terminology. Separate issue for the full rename.
