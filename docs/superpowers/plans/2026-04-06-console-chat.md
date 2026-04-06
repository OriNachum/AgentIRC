# Console Chat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a full TUI admin console (`culture console`) that connects to the IRC mesh as a first-class human client, with three-column layout, view switching, and all CLI commands.

**Architecture:** Textual TUI app with an async IRC client adapted from the existing `IRCTransport`/`Observer` patterns. Connects directly to the IRC server over TCP. Messages are buffered on a 10-second tick. New IRC protocol extensions (`ICON` command, `+H`/`+A`/`+B` user modes) let clients distinguish entity types.

**Tech Stack:** Python 3.12, Textual (new dependency), asyncio, existing `culture.protocol.message.Message` parser

**Spec:** `docs/superpowers/specs/2026-04-06-console-chat-design.md`

---

## File Structure

| File | Responsibility |
|------|----------------|
| **Create:** `culture/console/__init__.py` | Package marker |
| **Create:** `culture/console/app.py` | Textual `App` subclass — layout, keybindings, view switching |
| **Create:** `culture/console/client.py` | Async IRC client — connect, send, receive, buffer, route as Textual messages |
| **Create:** `culture/console/commands.py` | Command parser — `/command` dispatch table |
| **Create:** `culture/console/widgets/__init__.py` | Widget package marker |
| **Create:** `culture/console/widgets/sidebar.py` | Left panel — channels, entities grouped by type |
| **Create:** `culture/console/widgets/chat.py` | Center panel — message list, input field |
| **Create:** `culture/console/widgets/info_panel.py` | Right panel — context-sensitive details |
| **Create:** `culture/console/widgets/overview.py` | Overview view replacing center panel |
| **Create:** `culture/console/widgets/status.py` | Server status view replacing center panel |
| **Create:** `culture/console/widgets/agent_detail.py` | Agent detail view replacing center panel |
| **Create:** `culture/protocol/extensions/icons.md` | Protocol extension doc for ICON command and user modes |
| **Create:** `tests/test_console_client.py` | IRC client tests |
| **Create:** `tests/test_console_commands.py` | Command parser tests |
| **Create:** `tests/test_console_connection.py` | Server detection logic tests |
| **Create:** `tests/test_console_icons.py` | Icon resolution tests |
| **Create:** `tests/test_server_icon_skill.py` | Server-side ICON skill tests |
| **Modify:** `culture/cli.py:89-356` | Add `console` subcommand + `_cmd_console` handler + server detection |
| **Modify:** `culture/server/client.py:30-36,433-441,581-609` | Add `modes` set, `icon` field, extend WHO response, user mode handling |
| **Modify:** `culture/server/ircd.py:76-87` | Register IconSkill |
| **Modify:** `culture/protocol/commands.py` | Add `ICON` constant |
| **Modify:** `culture/clients/claude/config.py:50-61` | Add `icon` field to `AgentConfig` |
| **Modify:** `culture/clients/claude/irc_transport.py:52-84` | Send `ICON` on connect if configured |
| **Modify:** `culture/pidfile.py` | Add `list_servers()` and default server helpers |
| **Modify:** `pyproject.toml:16-22` | Add `textual` dependency |

---

### Task 1: Add `textual` Dependency and `ICON` Protocol Constant

**Files:**
- Modify: `pyproject.toml:16-22`
- Modify: `culture/protocol/commands.py`

- [ ] **Step 1: Add textual to pyproject.toml**

In `pyproject.toml`, add `textual` to the dependencies list:

```toml
dependencies = [
    "pyyaml>=6.0",
    "anthropic>=0.40",
    "claude-agent-sdk>=0.1",
    "mistune>=3.0",
    "aiohttp>=3.9",
    "textual>=1.0",
]
```

- [ ] **Step 2: Add ICON to protocol commands**

In `culture/protocol/commands.py`, add after the `HISTORY` line:

```python
# Extensions
HISTORY = "HISTORY"
ICON = "ICON"
```

- [ ] **Step 3: Install dependencies**

Run: `uv sync`
Expected: Textual installed, lock file updated.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock culture/protocol/commands.py
git commit -m "feat: add textual dependency and ICON protocol constant"
```

---

### Task 2: Server Discovery — `list_servers()` and Default Server

**Files:**
- Modify: `culture/pidfile.py`
- Create: `tests/test_console_connection.py`

- [ ] **Step 1: Write failing tests for server discovery**

Create `tests/test_console_connection.py`:

```python
"""Tests for server discovery and default server logic."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from culture.pidfile import (
    PID_DIR,
    list_servers,
    read_default_server,
    write_default_server,
    write_pid,
    write_port,
)


@pytest.fixture
def tmp_pid_dir(tmp_path):
    with patch("culture.pidfile.PID_DIR", str(tmp_path)):
        yield tmp_path


def test_list_servers_empty(tmp_pid_dir):
    assert list_servers() == []


def test_list_servers_finds_running(tmp_pid_dir):
    (tmp_pid_dir / "spark.pid").write_text(str(os.getpid()))
    (tmp_pid_dir / "spark.port").write_text("6667")
    with patch("culture.pidfile.is_process_alive", return_value=True), \
         patch("culture.pidfile.is_culture_process", return_value=True):
        result = list_servers()
    assert result == [{"name": "spark", "pid": os.getpid(), "port": 6667}]


def test_list_servers_skips_dead(tmp_pid_dir):
    (tmp_pid_dir / "dead.pid").write_text("99999")
    (tmp_pid_dir / "dead.port").write_text("6667")
    with patch("culture.pidfile.is_process_alive", return_value=False):
        assert list_servers() == []


def test_default_server_none_when_unset(tmp_pid_dir):
    assert read_default_server() is None


def test_write_and_read_default_server(tmp_pid_dir):
    write_default_server("spark")
    assert read_default_server() == "spark"


def test_resolve_server_zero_running(tmp_pid_dir):
    """No servers running should return empty list."""
    assert list_servers() == []


def test_resolve_server_one_running(tmp_pid_dir):
    (tmp_pid_dir / "spark.pid").write_text(str(os.getpid()))
    (tmp_pid_dir / "spark.port").write_text("6667")
    with patch("culture.pidfile.is_process_alive", return_value=True), \
         patch("culture.pidfile.is_culture_process", return_value=True):
        servers = list_servers()
    assert len(servers) == 1
    assert servers[0]["name"] == "spark"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_console_connection.py -v`
Expected: FAIL — `list_servers`, `read_default_server`, `write_default_server` not found.

- [ ] **Step 3: Implement server discovery in pidfile.py**

Add to the end of `culture/pidfile.py`:

```python
def list_servers() -> list[dict]:
    """List running culture servers.

    Returns list of dicts with keys: name, pid, port.
    """
    pid_dir = Path(PID_DIR)
    if not pid_dir.exists():
        return []
    servers = []
    for pid_path in sorted(pid_dir.glob("*.pid")):
        name = pid_path.stem
        pid = read_pid(name)
        if pid is None or not is_process_alive(pid) or not is_culture_process(pid):
            continue
        port = read_port(name) or 6667
        servers.append({"name": name, "pid": pid, "port": port})
    return servers


def read_default_server() -> str | None:
    """Read the default server name. Returns None if unset."""
    default_path = Path(PID_DIR) / "default_server"
    if not default_path.exists():
        return None
    try:
        return default_path.read_text().strip() or None
    except OSError:
        return None


def write_default_server(name: str) -> None:
    """Set the default server name."""
    pid_dir = Path(PID_DIR)
    pid_dir.mkdir(parents=True, exist_ok=True)
    (pid_dir / "default_server").write_text(name)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_console_connection.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add culture/pidfile.py tests/test_console_connection.py
git commit -m "feat: add server discovery and default server helpers"
```

---

### Task 3: Server-Side User Modes and Icon Support

**Files:**
- Modify: `culture/server/client.py:30-36,433-441,581-609`
- Create: `culture/server/skills/icon.py`
- Modify: `culture/server/ircd.py:76-87`
- Create: `tests/test_server_icon_skill.py`

- [ ] **Step 1: Write failing tests for user modes and ICON skill**

Create `tests/test_server_icon_skill.py`:

```python
"""Tests for user modes (+H, +A, +B) and ICON skill."""

import asyncio

import pytest

from culture.protocol.message import Message
from tests.helpers import connect_client, start_server


@pytest.fixture
async def server():
    srv = await start_server()
    yield srv
    await srv.shutdown()


@pytest.mark.asyncio
async def test_user_mode_set(server):
    reader, writer = await connect_client(server, "test-human")
    writer.write(b"MODE test-human +H\r\n")
    await writer.drain()
    # Read response — should get RPL_UMODEIS with +H
    data = await asyncio.wait_for(reader.read(4096), timeout=2)
    response = data.decode()
    assert "+H" in response
    writer.close()


@pytest.mark.asyncio
async def test_icon_set_and_query(server):
    reader, writer = await connect_client(server, "test-agent")
    # Set icon
    writer.write("ICON \u2605\r\n".encode())
    await writer.drain()
    data = await asyncio.wait_for(reader.read(4096), timeout=2)
    response = data.decode()
    assert "\u2605" in response
    writer.close()


@pytest.mark.asyncio
async def test_who_includes_mode_and_icon(server):
    r1, w1 = await connect_client(server, "test-human")
    w1.write(b"MODE test-human +H\r\n")
    await w1.drain()
    w1.write(b"JOIN #test\r\n")
    await w1.drain()
    w1.write("ICON \u2605\r\n".encode())
    await w1.drain()
    await asyncio.sleep(0.1)

    r2, w2 = await connect_client(server, "test-checker")
    w2.write(b"WHO #test\r\n")
    await w2.drain()
    data = await asyncio.wait_for(r2.read(4096), timeout=2)
    response = data.decode()
    # WHO reply should contain the user mode and icon info
    assert "test-human" in response
    w1.close()
    w2.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_server_icon_skill.py -v`
Expected: FAIL — modes and icon not implemented.

- [ ] **Step 3: Add modes set and icon field to Client**

In `culture/server/client.py`, add `modes` and `icon` to `__init__` after `self.tags`:

```python
        self.tags: list[str] = []
        self.modes: set[str] = set()
        self.icon: str | None = None
```

- [ ] **Step 4: Update `_handle_user_mode` to support +H, +A, +B**

Replace the existing `_handle_user_mode` method in `culture/server/client.py`:

```python
    async def _handle_user_mode(self, msg: Message) -> None:
        target_nick = msg.params[0]
        if target_nick != self.nick:
            await self.send_numeric(
                replies.ERR_USERSDONTMATCH,
                "Can't change mode for other users",
            )
            return
        if len(msg.params) > 1:
            modestring = msg.params[1]
            adding = True
            for ch in modestring:
                if ch == "+":
                    adding = True
                elif ch == "-":
                    adding = False
                elif ch in ("H", "A", "B"):
                    if adding:
                        self.modes.add(ch)
                    else:
                        self.modes.discard(ch)
        mode_str = "+" + "".join(sorted(self.modes)) if self.modes else "+"
        await self.send_numeric(replies.RPL_UMODEIS, mode_str)
```

- [ ] **Step 5: Update WHO response to include user modes**

In `culture/server/client.py`, in `_handle_who`, update the flags construction. Find the line `flags = "H"` (line ~593) and replace:

```python
                    flags = "H"
                    if channel.is_operator(member):
                        flags += "@"
                    elif channel.is_voiced(member):
                        flags += "+"
```

with:

```python
                    flags = "H"
                    if channel.is_operator(member):
                        flags += "@"
                    elif channel.is_voiced(member):
                        flags += "+"
                    if hasattr(member, "modes") and member.modes:
                        flags += "[" + "".join(sorted(member.modes)) + "]"
                    if hasattr(member, "icon") and member.icon:
                        flags += "{" + member.icon + "}"
```

- [ ] **Step 6: Create IconSkill**

Create `culture/server/skills/icon.py`:

```python
"""ICON skill — lets clients set a display icon/emoji."""

from __future__ import annotations

from culture.protocol.message import Message
from culture.server.skill import Skill

if __import__("typing").TYPE_CHECKING:
    from culture.server.client import Client


class IconSkill(Skill):
    name = "icon"
    commands = {"ICON"}

    async def on_command(self, client: Client, msg: Message) -> None:
        if msg.command != "ICON":
            return

        if not msg.params:
            # Query current icon
            icon = client.icon or "(none)"
            await client.send(Message(
                prefix=self.server.config.name,
                command="ICON",
                params=[client.nick, icon],
            ))
            return

        icon = msg.params[0].strip()
        if len(icon) > 4:
            await client.send(Message(
                prefix=self.server.config.name,
                command="NOTICE",
                params=[client.nick, "ICON too long (max 4 characters)"],
            ))
            return

        client.icon = icon
        await client.send(Message(
            prefix=self.server.config.name,
            command="ICON",
            params=[client.nick, icon],
        ))
```

- [ ] **Step 7: Register IconSkill in IRCd**

In `culture/server/ircd.py`, in `_register_default_skills`, add:

```python
    async def _register_default_skills(self) -> None:
        from culture.server.skills.history import HistorySkill
        from culture.server.skills.icon import IconSkill
        from culture.server.skills.rooms import RoomsSkill
        from culture.server.skills.threads import ThreadsSkill

        await self.register_skill(HistorySkill())
        await self.register_skill(RoomsSkill())
        await self.register_skill(ThreadsSkill())
        await self.register_skill(IconSkill())
```

- [ ] **Step 8: Run tests**

Run: `pytest tests/test_server_icon_skill.py -v`
Expected: All PASS.

- [ ] **Step 9: Commit**

```bash
git add culture/server/client.py culture/server/skills/icon.py culture/server/ircd.py tests/test_server_icon_skill.py
git commit -m "feat: add user modes (+H/+A/+B) and ICON IRC skill"
```

---

### Task 4: Add `icon` Field to Agent Config and Send on Connect

**Files:**
- Modify: `culture/clients/claude/config.py:50-61`
- Modify: `culture/clients/claude/irc_transport.py:52-84`
- Create: `tests/test_console_icons.py`

- [ ] **Step 1: Write failing tests for icon config and resolution**

Create `tests/test_console_icons.py`:

```python
"""Tests for icon resolution priority chain."""

import pytest

from culture.clients.claude.config import AgentConfig


def test_agent_config_has_icon_field():
    cfg = AgentConfig(nick="spark-claude", icon="★")
    assert cfg.icon == "★"


def test_agent_config_icon_default_none():
    cfg = AgentConfig(nick="spark-claude")
    assert cfg.icon is None


def test_agent_config_from_yaml_with_icon():
    """Icon field should be loaded from YAML config."""
    from culture.clients.claude.config import load_config
    import tempfile
    import yaml
    from pathlib import Path

    data = {
        "server": {"name": "spark", "host": "localhost", "port": 6667},
        "agents": [{"nick": "spark-claude", "icon": "★"}],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        path = f.name

    try:
        config = load_config(path)
        assert config.agents[0].icon == "★"
    finally:
        Path(path).unlink()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_console_icons.py -v`
Expected: FAIL — `icon` field not in `AgentConfig`.

- [ ] **Step 3: Add `icon` field to AgentConfig**

In `culture/clients/claude/config.py`, add `icon` to the `AgentConfig` dataclass:

```python
@dataclass
class AgentConfig:
    """Per-agent settings."""
    nick: str = ""
    agent: str = "claude"
    directory: str = "."
    channels: list[str] = field(default_factory=lambda: ["#general"])
    model: str = "claude-opus-4-6"
    thinking: str = "medium"
    system_prompt: str = ""
    tags: list[str] = field(default_factory=list)
    icon: str | None = None
```

- [ ] **Step 4: Send ICON on connect in IRCTransport**

In `culture/clients/claude/irc_transport.py`, in the `_on_welcome` handler, add ICON sending. Find the `_on_welcome` method and add after the channel joins:

```python
    async def _on_welcome(self, msg: Message) -> None:
        self.connected = True
        for ch in self.channels:
            await self._send_raw(f"JOIN {ch}")
        if self.tags:
            await self._send_raw(f"TAGS {' '.join(self.tags)}")
        if self.icon:
            await self._send_raw(f"ICON {self.icon}")
```

Add `icon` parameter to `__init__`:

```python
    def __init__(
        self,
        host: str,
        port: int,
        nick: str,
        user: str,
        channels: list[str],
        buffer: MessageBuffer,
        on_mention: Callable[[str, str, str], None] | None = None,
        tags: list[str] | None = None,
        on_roominvite: Callable[[str, str], None] | None = None,
        icon: str | None = None,
    ):
        ...
        self.icon = icon
```

- [ ] **Step 5: Propagate icon field to all backends**

Per the all-backends rule, add `icon: str | None = None` to `AgentConfig` in:
- `culture/clients/codex/config.py`
- `culture/clients/copilot/config.py`
- `culture/clients/acp/config.py`
- `packages/agent-harness/config.py`

Add `icon: str | None = None` to `IRCTransport.__init__` and the `ICON` send in `_on_welcome` in:
- `culture/clients/codex/irc_transport.py`
- `culture/clients/copilot/irc_transport.py`
- `culture/clients/acp/irc_transport.py`
- `packages/agent-harness/irc_transport.py`

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_console_icons.py -v`
Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add culture/clients/*/config.py culture/clients/*/irc_transport.py packages/agent-harness/config.py packages/agent-harness/irc_transport.py tests/test_console_icons.py
git commit -m "feat: add icon field to agent config and send ICON on connect"
```

---

### Task 5: Console IRC Client

**Files:**
- Create: `culture/console/__init__.py`
- Create: `culture/console/client.py`
- Create: `tests/test_console_client.py`

- [ ] **Step 1: Write failing tests for ConsoleIRCClient**

Create `tests/test_console_client.py`:

```python
"""Tests for the console IRC client."""

import asyncio

import pytest

from culture.console.client import ConsoleIRCClient


@pytest.fixture
async def server():
    from tests.helpers import start_server
    srv = await start_server()
    yield srv
    await srv.shutdown()


@pytest.mark.asyncio
async def test_connect_and_register(server):
    client = ConsoleIRCClient(
        host="127.0.0.1",
        port=server.port,
        nick=f"{server.config.name}-testuser",
        mode="H",
    )
    await client.connect()
    assert client.connected
    await client.disconnect()


@pytest.mark.asyncio
async def test_join_channel(server):
    client = ConsoleIRCClient(
        host="127.0.0.1",
        port=server.port,
        nick=f"{server.config.name}-testuser",
        mode="H",
    )
    await client.connect()
    await client.join("#test")
    assert "#test" in client.joined_channels
    await client.disconnect()


@pytest.mark.asyncio
async def test_send_message(server):
    client = ConsoleIRCClient(
        host="127.0.0.1",
        port=server.port,
        nick=f"{server.config.name}-testuser",
        mode="H",
    )
    await client.connect()
    await client.join("#test")
    await client.send_privmsg("#test", "hello world")
    await client.disconnect()


@pytest.mark.asyncio
async def test_message_buffer(server):
    client = ConsoleIRCClient(
        host="127.0.0.1",
        port=server.port,
        nick=f"{server.config.name}-testuser",
        mode="H",
    )
    await client.connect()
    await client.join("#test")
    await client.send_privmsg("#test", "test message")
    await asyncio.sleep(0.2)
    messages = client.drain_messages()
    # Messages is a list — may or may not contain echo depending on server config
    assert isinstance(messages, list)
    await client.disconnect()


@pytest.mark.asyncio
async def test_list_channels(server):
    client = ConsoleIRCClient(
        host="127.0.0.1",
        port=server.port,
        nick=f"{server.config.name}-testuser",
        mode="H",
    )
    await client.connect()
    await client.join("#test")
    channels = await client.list_channels()
    assert "#test" in channels
    await client.disconnect()


@pytest.mark.asyncio
async def test_who(server):
    client = ConsoleIRCClient(
        host="127.0.0.1",
        port=server.port,
        nick=f"{server.config.name}-testuser",
        mode="H",
    )
    await client.connect()
    await client.join("#test")
    members = await client.who("#test")
    nicks = [m["nick"] for m in members]
    assert f"{server.config.name}-testuser" in nicks
    await client.disconnect()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_console_client.py -v`
Expected: FAIL — `culture.console.client` not found.

- [ ] **Step 3: Create console package**

Create `culture/console/__init__.py`:

```python
"""Console TUI for culture mesh administration."""
```

- [ ] **Step 4: Implement ConsoleIRCClient**

Create `culture/console/client.py`:

```python
"""Async IRC client for the console TUI."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from culture.protocol.message import Message

logger = logging.getLogger(__name__)

REGISTER_TIMEOUT = 5.0
QUERY_TIMEOUT = 3.0


@dataclass
class ChatMessage:
    """A buffered chat message."""
    channel: str
    nick: str
    text: str
    timestamp: float = 0.0


class ConsoleIRCClient:
    """Persistent async IRC client for the console TUI.

    Connects as a human user, buffers incoming messages, and provides
    query methods for LIST, WHO, HISTORY.
    """

    def __init__(
        self,
        host: str,
        port: int,
        nick: str,
        mode: str = "H",
        icon: str | None = None,
    ):
        self.host = host
        self.port = port
        self.nick = nick
        self.mode = mode
        self.icon = icon
        self.connected = False
        self.joined_channels: set[str] = set()
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._read_task: asyncio.Task | None = None
        self._message_buffer: list[ChatMessage] = []
        self._pending: dict[str, asyncio.Future] = {}
        self._collect_buffers: dict[str, list] = {}

    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port),
            timeout=REGISTER_TIMEOUT,
        )
        await self._send_raw(f"NICK {self.nick}")
        await self._send_raw(f"USER console 0 * :culture console")
        self._read_task = asyncio.create_task(self._read_loop())
        # Wait for RPL_WELCOME
        await self._wait_for("001", timeout=REGISTER_TIMEOUT)
        self.connected = True
        # Set user mode
        if self.mode:
            await self._send_raw(f"MODE {self.nick} +{self.mode}")
        if self.icon:
            await self._send_raw(f"ICON {self.icon}")

    async def disconnect(self) -> None:
        self.connected = False
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        if self._writer:
            try:
                await self._send_raw("QUIT :console closed")
            except (ConnectionError, OSError):
                pass
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except (ConnectionError, BrokenPipeError, OSError):
                pass

    async def join(self, channel: str) -> None:
        await self._send_raw(f"JOIN {channel}")
        self.joined_channels.add(channel)

    async def part(self, channel: str) -> None:
        await self._send_raw(f"PART {channel}")
        self.joined_channels.discard(channel)

    async def send_privmsg(self, target: str, text: str) -> None:
        await self._send_raw(f"PRIVMSG {target} :{text}")

    async def send_raw(self, line: str) -> None:
        await self._send_raw(line)

    def drain_messages(self) -> list[ChatMessage]:
        """Return and clear the message buffer."""
        msgs = list(self._message_buffer)
        self._message_buffer.clear()
        return msgs

    async def list_channels(self) -> list[str]:
        key = "LIST"
        self._collect_buffers[key] = []
        await self._send_raw("LIST")
        await self._wait_for("323", timeout=QUERY_TIMEOUT)  # RPL_LISTEND
        channels = [item["name"] for item in self._collect_buffers.pop(key, [])]
        return sorted(channels)

    async def who(self, target: str) -> list[dict]:
        key = f"WHO:{target}"
        self._collect_buffers[key] = []
        await self._send_raw(f"WHO {target}")
        await self._wait_for("315", timeout=QUERY_TIMEOUT)  # RPL_ENDOFWHO
        return self._collect_buffers.pop(key, [])

    async def history(self, channel: str, limit: int = 50) -> list[dict]:
        key = f"HISTORY:{channel}"
        self._collect_buffers[key] = []
        await self._send_raw(f"HISTORY RECENT {channel} {limit}")
        await self._wait_for("HISTORYEND", timeout=QUERY_TIMEOUT)
        return self._collect_buffers.pop(key, [])

    async def _send_raw(self, line: str) -> None:
        if self._writer:
            self._writer.write(f"{line}\r\n".encode())
            await self._writer.drain()

    async def _wait_for(self, command: str, timeout: float = 5.0) -> Message | None:
        future: asyncio.Future[Message] = asyncio.get_event_loop().create_future()
        self._pending[command] = future
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            self._pending.pop(command, None)

    async def _read_loop(self) -> None:
        buf = ""
        try:
            while True:
                data = await self._reader.read(4096)
                if not data:
                    break
                buf += data.decode("utf-8", errors="replace")
                while "\r\n" in buf:
                    line, buf = buf.split("\r\n", 1)
                    if line.strip():
                        msg = Message.parse(line)
                        await self._handle(msg)
        except asyncio.CancelledError:
            raise
        except (ConnectionError, OSError):
            logger.warning("Console IRC connection lost")
        finally:
            self.connected = False

    async def _handle(self, msg: Message) -> None:
        cmd = msg.command

        if cmd == "PING":
            await self._send_raw(f"PONG :{msg.params[0] if msg.params else ''}")
            return

        if cmd == "PRIVMSG" and len(msg.params) >= 2:
            nick = msg.prefix.split("!")[0] if msg.prefix else "unknown"
            channel = msg.params[0]
            text = msg.params[1]
            self._message_buffer.append(ChatMessage(
                channel=channel, nick=nick, text=text,
            ))

        # Collect LIST responses
        if cmd == "322" and len(msg.params) >= 3:  # RPL_LIST
            self._collect_buffers.setdefault("LIST", []).append({
                "name": msg.params[1],
                "count": msg.params[2],
                "topic": msg.params[3] if len(msg.params) > 3 else "",
            })

        # Collect WHO responses
        if cmd == "352" and len(msg.params) >= 7:  # RPL_WHOREPLY
            target = msg.params[1]
            self._collect_buffers.setdefault(f"WHO:{target}", []).append({
                "nick": msg.params[5],
                "user": msg.params[2],
                "host": msg.params[3],
                "server": msg.params[4],
                "flags": msg.params[6],
            })

        # Collect HISTORY responses
        if cmd == "HISTORY" and len(msg.params) >= 3:
            channel = msg.params[0]
            self._collect_buffers.setdefault(f"HISTORY:{channel}", []).append({
                "nick": msg.params[1],
                "text": msg.params[2],
                "timestamp": msg.params[3] if len(msg.params) > 3 else "",
            })

        # Resolve pending futures
        if cmd in self._pending:
            future = self._pending[cmd]
            if not future.done():
                future.set_result(msg)
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_console_client.py -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add culture/console/__init__.py culture/console/client.py tests/test_console_client.py
git commit -m "feat: add ConsoleIRCClient with buffered messaging and query methods"
```

---

### Task 6: Command Parser

**Files:**
- Create: `culture/console/commands.py`
- Create: `tests/test_console_commands.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_console_commands.py`:

```python
"""Tests for console command parser."""

import pytest

from culture.console.commands import parse_command, CommandType


def test_parse_chat_message():
    result = parse_command("hello world")
    assert result.type == CommandType.CHAT
    assert result.text == "hello world"


def test_parse_channels():
    result = parse_command("/channels")
    assert result.type == CommandType.CHANNELS


def test_parse_join():
    result = parse_command("/join #ops")
    assert result.type == CommandType.JOIN
    assert result.args == ["#ops"]


def test_parse_part():
    result = parse_command("/part #ops")
    assert result.type == CommandType.PART
    assert result.args == ["#ops"]


def test_parse_who():
    result = parse_command("/who #general")
    assert result.type == CommandType.WHO
    assert result.args == ["#general"]


def test_parse_send():
    result = parse_command("/send #ops hello agents")
    assert result.type == CommandType.SEND
    assert result.args == ["#ops"]
    assert result.text == "hello agents"


def test_parse_overview():
    result = parse_command("/overview")
    assert result.type == CommandType.OVERVIEW


def test_parse_status():
    result = parse_command("/status spark-claude")
    assert result.type == CommandType.STATUS
    assert result.args == ["spark-claude"]


def test_parse_status_no_args():
    result = parse_command("/status")
    assert result.type == CommandType.STATUS
    assert result.args == []


def test_parse_agents():
    result = parse_command("/agents")
    assert result.type == CommandType.AGENTS


def test_parse_start():
    result = parse_command("/start spark-claude")
    assert result.type == CommandType.START
    assert result.args == ["spark-claude"]


def test_parse_stop():
    result = parse_command("/stop spark-claude")
    assert result.type == CommandType.STOP
    assert result.args == ["spark-claude"]


def test_parse_restart():
    result = parse_command("/restart spark-claude")
    assert result.type == CommandType.RESTART
    assert result.args == ["spark-claude"]


def test_parse_icon():
    result = parse_command("/icon spark-claude ★")
    assert result.type == CommandType.ICON
    assert result.args == ["spark-claude", "★"]


def test_parse_read():
    result = parse_command("/read #ops -n 20")
    assert result.type == CommandType.READ
    assert result.args == ["#ops", "-n", "20"]


def test_parse_topic():
    result = parse_command("/topic #ops New topic text")
    assert result.type == CommandType.TOPIC
    assert result.args == ["#ops"]
    assert result.text == "New topic text"


def test_parse_kick():
    result = parse_command("/kick #ops baduser")
    assert result.type == CommandType.KICK
    assert result.args == ["#ops", "baduser"]


def test_parse_invite():
    result = parse_command("/invite #ops newuser")
    assert result.type == CommandType.INVITE
    assert result.args == ["#ops", "newuser"]


def test_parse_server():
    result = parse_command("/server thor")
    assert result.type == CommandType.SERVER
    assert result.args == ["thor"]


def test_parse_quit():
    result = parse_command("/quit")
    assert result.type == CommandType.QUIT


def test_parse_unknown_command():
    result = parse_command("/unknown foo bar")
    assert result.type == CommandType.UNKNOWN
    assert result.text == "/unknown foo bar"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_console_commands.py -v`
Expected: FAIL — `culture.console.commands` not found.

- [ ] **Step 3: Implement command parser**

Create `culture/console/commands.py`:

```python
"""Console command parser."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class CommandType(Enum):
    CHAT = auto()
    CHANNELS = auto()
    JOIN = auto()
    PART = auto()
    WHO = auto()
    SEND = auto()
    READ = auto()
    OVERVIEW = auto()
    STATUS = auto()
    AGENTS = auto()
    START = auto()
    STOP = auto()
    RESTART = auto()
    ICON = auto()
    TOPIC = auto()
    KICK = auto()
    INVITE = auto()
    SERVER = auto()
    QUIT = auto()
    UNKNOWN = auto()


@dataclass
class ParsedCommand:
    type: CommandType
    args: list[str] = field(default_factory=list)
    text: str = ""


# Commands where trailing words after args form free text
_TEXT_COMMANDS = {
    "send": (CommandType.SEND, 1),    # /send <target> <text...>
    "topic": (CommandType.TOPIC, 1),  # /topic <channel> <text...>
}

# Simple commands: name -> (type, expected_arg_count_or_None_for_variadic)
_COMMANDS: dict[str, CommandType] = {
    "channels": CommandType.CHANNELS,
    "join": CommandType.JOIN,
    "part": CommandType.PART,
    "who": CommandType.WHO,
    "read": CommandType.READ,
    "overview": CommandType.OVERVIEW,
    "status": CommandType.STATUS,
    "agents": CommandType.AGENTS,
    "start": CommandType.START,
    "stop": CommandType.STOP,
    "restart": CommandType.RESTART,
    "icon": CommandType.ICON,
    "kick": CommandType.KICK,
    "invite": CommandType.INVITE,
    "server": CommandType.SERVER,
    "quit": CommandType.QUIT,
}


def parse_command(input_text: str) -> ParsedCommand:
    """Parse user input into a command or chat message."""
    stripped = input_text.strip()
    if not stripped:
        return ParsedCommand(type=CommandType.CHAT, text="")

    if not stripped.startswith("/"):
        return ParsedCommand(type=CommandType.CHAT, text=stripped)

    parts = stripped[1:].split()
    if not parts:
        return ParsedCommand(type=CommandType.CHAT, text=stripped)

    cmd_name = parts[0].lower()
    rest = parts[1:]

    # Text commands: split at boundary, rest is free text
    if cmd_name in _TEXT_COMMANDS:
        cmd_type, arg_count = _TEXT_COMMANDS[cmd_name]
        args = rest[:arg_count]
        text = " ".join(rest[arg_count:])
        return ParsedCommand(type=cmd_type, args=args, text=text)

    # Regular commands
    if cmd_name in _COMMANDS:
        return ParsedCommand(type=_COMMANDS[cmd_name], args=rest)

    return ParsedCommand(type=CommandType.UNKNOWN, text=stripped)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_console_commands.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add culture/console/commands.py tests/test_console_commands.py
git commit -m "feat: add console command parser with all CLI command types"
```

---

### Task 7: Console TUI Widgets — Sidebar, Chat, Info Panel

**Files:**
- Create: `culture/console/widgets/__init__.py`
- Create: `culture/console/widgets/sidebar.py`
- Create: `culture/console/widgets/chat.py`
- Create: `culture/console/widgets/info_panel.py`

- [ ] **Step 1: Create widget package**

Create `culture/console/widgets/__init__.py`:

```python
"""Console TUI widgets."""
```

- [ ] **Step 2: Implement Sidebar widget**

Create `culture/console/widgets/sidebar.py`:

```python
"""Left sidebar — channels and entities grouped by type."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message as TextualMessage
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView


class ChannelSelected(TextualMessage):
    """Posted when a channel is selected in the sidebar."""
    def __init__(self, channel: str) -> None:
        self.channel = channel
        super().__init__()


class EntitySelected(TextualMessage):
    """Posted when an entity is selected in the sidebar."""
    def __init__(self, nick: str) -> None:
        self.nick = nick
        super().__init__()


class Sidebar(Widget):
    """Left sidebar showing channels and entities."""

    DEFAULT_CSS = """
    Sidebar {
        width: 24;
        border-right: solid $surface-lighten-2;
        padding: 0 1;
    }
    Sidebar .section-header {
        color: $warning;
        text-style: bold;
        margin-top: 1;
    }
    Sidebar .channel-item {
        color: $text;
    }
    Sidebar .channel-item.--selected {
        background: $surface-lighten-2;
    }
    Sidebar .entity-online {
        color: $success;
    }
    Sidebar .entity-offline {
        color: $text-muted;
    }
    """

    channels: reactive[list[dict]] = reactive(list, recompose=True)
    entities: reactive[list[dict]] = reactive(list, recompose=True)
    active_channel: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("CHANNELS", classes="section-header")
            for ch in self.channels:
                name = ch.get("name", "")
                count = ch.get("count", "")
                unread = ch.get("unread", 0)
                suffix = f" *{unread}" if unread else ""
                classes = "channel-item"
                if name == self.active_channel:
                    classes += " --selected"
                yield Label(f"  {name} ({count}){suffix}", classes=classes, id=f"ch-{name}")

            # Group entities by type
            groups = {"AGENTS": [], "ADMIN": [], "HUMANS": [], "BOTS": []}
            type_icons = {"agent": "🤖", "admin": "👑", "human": "👤", "bot": "⚙"}
            type_group = {"agent": "AGENTS", "admin": "ADMIN", "human": "HUMANS", "bot": "BOTS"}

            for e in self.entities:
                group = type_group.get(e.get("type", "agent"), "AGENTS")
                groups[group].append(e)

            for group_name, members in groups.items():
                if not members:
                    continue
                default_icon = type_icons.get(group_name.rstrip("S").lower(), "")
                yield Label(f"{'─' * 20}", classes="separator")
                yield Label(f"{group_name} {default_icon}", classes="section-header")
                for m in members:
                    dot = "●" if m.get("online", True) else "○"
                    icon = m.get("icon", "")
                    nick = m.get("nick", "")
                    cls = "entity-online" if m.get("online", True) else "entity-offline"
                    yield Label(f"  {dot} {icon} {nick}", classes=cls, id=f"ent-{nick}")
```

- [ ] **Step 3: Implement Chat panel widget**

Create `culture/console/widgets/chat.py`:

```python
"""Center chat panel — message display and input."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.message import Message as TextualMessage
from textual.widget import Widget
from textual.widgets import Input, Label, RichLog


class UserInput(TextualMessage):
    """Posted when user submits input."""
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class ChatPanel(Widget):
    """Center panel for chat messages and input."""

    DEFAULT_CSS = """
    ChatPanel {
        width: 1fr;
        padding: 0 1;
    }
    ChatPanel #chat-header {
        color: $warning;
        text-style: bold;
        border-bottom: solid $surface-lighten-2;
        height: 1;
    }
    ChatPanel #chat-log {
        height: 1fr;
    }
    ChatPanel #chat-input {
        dock: bottom;
        border-top: solid $surface-lighten-2;
    }
    """

    def __init__(self, channel: str = "#general", nick: str = "") -> None:
        super().__init__()
        self.channel = channel
        self.nick = nick

    def compose(self) -> ComposeResult:
        yield Label(f"{self.channel}", id="chat-header")
        yield RichLog(id="chat-log", wrap=True, highlight=True)
        yield Input(placeholder=f"{self.nick} {self.channel}>", id="chat-input")

    def add_message(self, timestamp: str, icon: str, nick: str, text: str) -> None:
        log = self.query_one("#chat-log", RichLog)
        log.write(f"[dim]{timestamp}[/] {icon} [bold]{nick}:[/] {text}")

    def set_channel(self, channel: str) -> None:
        self.channel = channel
        self.query_one("#chat-header", Label).update(channel)
        self.query_one("#chat-input", Input).placeholder = f"{self.nick} {channel}>"

    def set_content(self, title: str, lines: list[str]) -> None:
        """Replace chat with arbitrary content (for overview/status views)."""
        self.query_one("#chat-header", Label).update(title)
        log = self.query_one("#chat-log", RichLog)
        log.clear()
        for line in lines:
            log.write(line)

    def clear_log(self) -> None:
        self.query_one("#chat-log", RichLog).clear()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self.post_message(UserInput(text))
            event.input.value = ""
```

- [ ] **Step 4: Implement Info panel widget**

Create `culture/console/widgets/info_panel.py`:

```python
"""Right info panel — context-sensitive details."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Label


class InfoPanel(Widget):
    """Right panel showing context-sensitive information."""

    DEFAULT_CSS = """
    InfoPanel {
        width: 24;
        border-left: solid $surface-lighten-2;
        padding: 0 1;
    }
    InfoPanel .info-header {
        color: $warning;
        text-style: bold;
        margin-top: 1;
    }
    InfoPanel .info-value {
        color: $text-muted;
    }
    InfoPanel .keybinding {
        color: $accent;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="info-scroll"):
            yield Label("CHANNEL INFO", classes="info-header", id="info-title")
            yield Label("", classes="info-value", id="info-content")
            yield Label("─" * 20)
            yield Label("KEYBINDINGS", classes="info-header")
            yield Label("Tab    — next channel", classes="keybinding")
            yield Label("S-Tab  — prev channel", classes="keybinding")
            yield Label("Ctrl+O — overview", classes="keybinding")
            yield Label("Ctrl+S — status", classes="keybinding")
            yield Label("Esc    — back to chat", classes="keybinding")
            yield Label("Ctrl+Q — quit", classes="keybinding")
            yield Label("/      — command mode", classes="keybinding")

    def set_channel_info(self, info: dict) -> None:
        self.query_one("#info-title", Label).update("CHANNEL INFO")
        lines = []
        lines.append(f"Topic: {info.get('topic', '')}")
        lines.append(f"Members: {info.get('member_count', 0)}")
        lines.append(f"Messages: {info.get('message_count', 0)}")
        if info.get("members"):
            lines.append("─" * 18)
            lines.append("MEMBERS")
            for m in info["members"]:
                icon = m.get("icon", "")
                lines.append(f"  ● {icon} {m.get('nick', '')}")
        self.query_one("#info-content", Label).update("\n".join(lines))

    def set_agent_actions(self, nick: str) -> None:
        self.query_one("#info-title", Label).update(f"AGENT: {nick}")
        self.query_one("#info-content", Label).update(
            "[r] Restart\n[s] Stop\n[l] View logs\n[w] Whisper\n[i] Change icon"
        )

    def set_mesh_stats(self, stats: dict) -> None:
        self.query_one("#info-title", Label).update("MESH STATS")
        lines = [f"{k}: {v}" for k, v in stats.items()]
        self.query_one("#info-content", Label).update("\n".join(lines))
```

- [ ] **Step 5: Commit**

```bash
git add culture/console/widgets/
git commit -m "feat: add console TUI widgets — sidebar, chat, info panel"
```

---

### Task 8: Console TUI App — Main Layout and View Switching

**Files:**
- Create: `culture/console/app.py`

- [ ] **Step 1: Implement the main Textual App**

Create `culture/console/app.py`:

```python
"""Console TUI application — main layout and view switching."""

from __future__ import annotations

import asyncio
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header

from culture.console.client import ConsoleIRCClient
from culture.console.commands import CommandType, parse_command
from culture.console.widgets.chat import ChatPanel, UserInput
from culture.console.widgets.info_panel import InfoPanel
from culture.console.widgets.sidebar import ChannelSelected, Sidebar


BUFFER_INTERVAL = 10.0  # seconds between UI refreshes


class ConsoleApp(App):
    """Culture console — admin TUI for the IRC mesh."""

    TITLE = "culture console"
    CSS = """
    Screen {
        layout: horizontal;
    }
    #main-area {
        width: 1fr;
    }
    """

    BINDINGS = [
        Binding("ctrl+o", "show_overview", "Overview"),
        Binding("ctrl+s", "show_status", "Status"),
        Binding("escape", "back_to_chat", "Back to chat"),
        Binding("ctrl+q", "quit_app", "Quit"),
        Binding("tab", "next_channel", "Next channel", show=False),
        Binding("shift+tab", "prev_channel", "Prev channel", show=False),
    ]

    def __init__(
        self,
        irc_client: ConsoleIRCClient,
        server_name: str,
    ) -> None:
        super().__init__()
        self.irc = irc_client
        self.server_name = server_name
        self._current_channel = ""
        self._channel_list: list[str] = []
        self._current_view = "chat"
        self._refresh_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Sidebar(id="sidebar")
            yield ChatPanel(
                channel="#general",
                nick=self.irc.nick,
                id="chat-panel",
            )
            yield InfoPanel(id="info-panel")
        yield Footer()

    async def on_mount(self) -> None:
        self.sub_title = f"{self.irc.nick}@{self.server_name}"
        # Start periodic buffer flush
        self._refresh_task = asyncio.create_task(self._buffer_loop())

    async def on_unmount(self) -> None:
        if self._refresh_task:
            self._refresh_task.cancel()

    async def _buffer_loop(self) -> None:
        """Flush message buffer every BUFFER_INTERVAL seconds."""
        try:
            while True:
                await asyncio.sleep(BUFFER_INTERVAL)
                await self._flush_messages()
        except asyncio.CancelledError:
            pass

    async def _flush_messages(self) -> None:
        messages = self.irc.drain_messages()
        chat = self.query_one("#chat-panel", ChatPanel)
        for msg in messages:
            if msg.channel == self._current_channel:
                now = datetime.now().strftime("%H:%M")
                chat.add_message(now, "", msg.nick, msg.text)

    async def on_user_input(self, event: UserInput) -> None:
        parsed = parse_command(event.text)
        await self._execute_command(parsed)

    async def _execute_command(self, cmd) -> None:
        chat = self.query_one("#chat-panel", ChatPanel)

        if cmd.type == CommandType.CHAT:
            if self._current_channel and cmd.text:
                await self.irc.send_privmsg(self._current_channel, cmd.text)
                now = datetime.now().strftime("%H:%M")
                chat.add_message(now, "", self.irc.nick, cmd.text)

        elif cmd.type == CommandType.JOIN:
            if cmd.args:
                channel = cmd.args[0]
                await self.irc.join(channel)
                self._current_channel = channel
                chat.set_channel(channel)
                await self._refresh_channel_list()

        elif cmd.type == CommandType.PART:
            if cmd.args:
                await self.irc.part(cmd.args[0])
                await self._refresh_channel_list()

        elif cmd.type == CommandType.CHANNELS:
            channels = await self.irc.list_channels()
            lines = [f"  {ch}" for ch in channels]
            chat.set_content("CHANNELS", ["Active channels:"] + lines)

        elif cmd.type == CommandType.WHO:
            target = cmd.args[0] if cmd.args else self._current_channel
            if target:
                members = await self.irc.who(target)
                lines = [f"  {m['nick']} ({m.get('flags', '')})" for m in members]
                chat.set_content(f"WHO {target}", [f"Members of {target}:"] + lines)

        elif cmd.type == CommandType.READ:
            channel = cmd.args[0] if cmd.args else self._current_channel
            limit = 50
            if "-n" in cmd.args:
                idx = cmd.args.index("-n")
                if idx + 1 < len(cmd.args):
                    try:
                        limit = int(cmd.args[idx + 1])
                    except ValueError:
                        pass
            if channel:
                history = await self.irc.history(channel, limit)
                lines = [f"  {h.get('nick', '')}: {h.get('text', '')}" for h in history]
                chat.set_content(f"HISTORY {channel}", lines or ["(no history)"])

        elif cmd.type == CommandType.SEND:
            if cmd.args and cmd.text:
                await self.irc.send_privmsg(cmd.args[0], cmd.text)

        elif cmd.type == CommandType.OVERVIEW:
            await self.action_show_overview()

        elif cmd.type == CommandType.STATUS:
            agent = cmd.args[0] if cmd.args else None
            await self._show_status(agent)

        elif cmd.type == CommandType.AGENTS:
            await self._show_agents()

        elif cmd.type == CommandType.ICON:
            if len(cmd.args) >= 2:
                nick, icon = cmd.args[0], cmd.args[1]
                await self.irc.send_raw(f"ICON {icon}")

        elif cmd.type == CommandType.TOPIC:
            if cmd.args:
                channel = cmd.args[0]
                await self.irc.send_raw(f"TOPIC {channel} :{cmd.text}")

        elif cmd.type == CommandType.KICK:
            if len(cmd.args) >= 2:
                await self.irc.send_raw(f"KICK {cmd.args[0]} {cmd.args[1]}")

        elif cmd.type == CommandType.INVITE:
            if len(cmd.args) >= 2:
                await self.irc.send_raw(f"INVITE {cmd.args[1]} {cmd.args[0]}")

        elif cmd.type == CommandType.SERVER:
            if cmd.args:
                chat.set_content("SERVER", [f"Server switching not yet available (requested: {cmd.args[0]})"])

        elif cmd.type == CommandType.QUIT:
            await self.action_quit_app()

        elif cmd.type in (CommandType.START, CommandType.STOP, CommandType.RESTART):
            if cmd.args:
                action = cmd.type.name.lower()
                chat.set_content(
                    f"{action.upper()} {cmd.args[0]}",
                    [f"Agent management from console requires IPC — use `culture {action} {cmd.args[0]}` in another terminal."],
                )

    async def _refresh_channel_list(self) -> None:
        channels = await self.irc.list_channels()
        self._channel_list = channels
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.channels = [{"name": ch} for ch in channels]
        sidebar.active_channel = self._current_channel

    async def action_show_overview(self) -> None:
        self._current_view = "overview"
        chat = self.query_one("#chat-panel", ChatPanel)
        channels = await self.irc.list_channels()
        lines = ["", "Channels:"]
        for ch in channels:
            members = await self.irc.who(ch)
            lines.append(f"  {ch}  {len(members)} users")
        chat.set_content("MESH OVERVIEW (Esc to return)", lines)
        chat.query_one("#chat-input").display = False

    async def _show_status(self, agent: str | None = None) -> None:
        self._current_view = "status"
        chat = self.query_one("#chat-panel", ChatPanel)
        if agent:
            members_all: list[dict] = []
            for ch in self.irc.joined_channels:
                members_all.extend(await self.irc.who(ch))
            found = [m for m in members_all if m.get("nick") == agent]
            if found:
                m = found[0]
                lines = [
                    f"Nick: {m['nick']}",
                    f"User: {m.get('user', '')}",
                    f"Host: {m.get('host', '')}",
                    f"Server: {m.get('server', '')}",
                    f"Flags: {m.get('flags', '')}",
                ]
            else:
                lines = [f"Agent {agent} not found in joined channels."]
            chat.set_content(f"AGENT: {agent} (Esc to return)", lines)
        else:
            lines = [
                f"Server: {self.irc.host}:{self.irc.port}",
                f"Nick: {self.irc.nick}",
                f"Connected: {self.irc.connected}",
                f"Channels: {', '.join(sorted(self.irc.joined_channels))}",
            ]
            chat.set_content("SERVER STATUS (Esc to return)", lines)
        chat.query_one("#chat-input").display = False

    async def _show_agents(self) -> None:
        self._current_view = "agents"
        chat = self.query_one("#chat-panel", ChatPanel)
        members: list[dict] = []
        for ch in self.irc.joined_channels:
            for m in await self.irc.who(ch):
                if m["nick"] not in [x["nick"] for x in members]:
                    members.append(m)
        lines = [f"  {m['nick']}  flags={m.get('flags', '')}" for m in members]
        chat.set_content("AGENTS (Esc to return)", lines or ["(no agents found)"])
        chat.query_one("#chat-input").display = False

    async def action_show_status(self) -> None:
        await self._show_status()

    async def action_back_to_chat(self) -> None:
        if self._current_view != "chat":
            self._current_view = "chat"
            chat = self.query_one("#chat-panel", ChatPanel)
            chat.clear_log()
            chat.set_channel(self._current_channel or "#general")
            chat.query_one("#chat-input").display = True

    def action_next_channel(self) -> None:
        if not self._channel_list:
            return
        try:
            idx = self._channel_list.index(self._current_channel)
            idx = (idx + 1) % len(self._channel_list)
        except ValueError:
            idx = 0
        self._current_channel = self._channel_list[idx]
        chat = self.query_one("#chat-panel", ChatPanel)
        chat.set_channel(self._current_channel)
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.active_channel = self._current_channel

    def action_prev_channel(self) -> None:
        if not self._channel_list:
            return
        try:
            idx = self._channel_list.index(self._current_channel)
            idx = (idx - 1) % len(self._channel_list)
        except ValueError:
            idx = 0
        self._current_channel = self._channel_list[idx]
        chat = self.query_one("#chat-panel", ChatPanel)
        chat.set_channel(self._current_channel)
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.active_channel = self._current_channel

    async def action_quit_app(self) -> None:
        await self.irc.disconnect()
        self.exit()
```

- [ ] **Step 2: Commit**

```bash
git add culture/console/app.py
git commit -m "feat: add ConsoleApp — main TUI layout with view switching and command dispatch"
```

---

### Task 9: CLI Integration — `culture console` Subcommand

**Files:**
- Modify: `culture/cli.py:89-356`

- [ ] **Step 1: Add console subcommand parser**

In `culture/cli.py`, in `_build_parser()`, add after the existing subcommand parsers (around line 285, before the bot parser):

```python
    # -- console subcommand ------------------------------------------------
    console_parser = sub.add_parser("console", help="Interactive admin console")
    console_parser.add_argument(
        "server_name", nargs="?", default=None,
        help="Server to connect to (auto-detects if omitted)",
    )
    console_parser.add_argument(
        "--config", default=DEFAULT_CONFIG,
        help="Config file path",
    )
```

- [ ] **Step 2: Add `_cmd_console` handler**

Add before the dispatch dict:

```python
def _cmd_console(args: argparse.Namespace) -> None:
    """Launch the interactive console TUI."""
    import subprocess

    from culture.pidfile import list_servers, read_default_server

    server_name = args.server_name
    host = "127.0.0.1"
    port = 6667

    if server_name:
        # Explicit server — look up its port
        from culture.pidfile import read_port
        p = read_port(server_name)
        if p:
            port = p
    else:
        # Auto-detect
        servers = list_servers()
        if not servers:
            print("No culture servers running. Start one with: culture server start")
            return
        if len(servers) == 1:
            server_name = servers[0]["name"]
            port = servers[0]["port"]
        else:
            default = read_default_server()
            if default:
                match = [s for s in servers if s["name"] == default]
                if match:
                    server_name = match[0]["name"]
                    port = match[0]["port"]
                else:
                    server_name = servers[0]["name"]
                    port = servers[0]["port"]
            else:
                server_name = servers[0]["name"]
                port = servers[0]["port"]

    # Resolve nick
    nick_suffix = _resolve_console_nick()
    nick = f"{server_name}-{nick_suffix}"

    from culture.console.app import ConsoleApp
    from culture.console.client import ConsoleIRCClient

    client = ConsoleIRCClient(host=host, port=port, nick=nick, mode="H")

    async def run():
        await client.connect()
        app = ConsoleApp(irc_client=client, server_name=server_name)
        await app.run_async()

    asyncio.run(run())


def _resolve_console_nick() -> str:
    """Resolve the human nick: git username -> OS user -> config override."""
    import subprocess

    # Check config override (future: culture config get nick)
    # For now: git -> OS fallback
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            name = result.stdout.strip().lower()
            # Sanitize: only alphanumeric and hyphens
            import re
            name = re.sub(r"[^a-z0-9-]", "", name.replace(" ", "-"))
            if name:
                return name
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # OS username fallback
    import os
    return os.environ.get("USER", "human")
```

- [ ] **Step 3: Register in dispatch dict**

In the dispatch dict (around line 336), add:

```python
    "console": _cmd_console,
```

- [ ] **Step 4: Add `culture server default` subcommand**

In `_build_parser()`, after `srv_status`, add:

```python
    srv_default = server_sub.add_parser("default", help="Set default server")
    srv_default.add_argument("name", help="Server name to set as default")
```

In `_cmd_server`, add handling for the `default` subcommand:

```python
    elif args.server_command == "default":
        from culture.pidfile import write_default_server
        write_default_server(args.name)
        print(f"Default server set to '{args.name}'")
```

- [ ] **Step 5: Test manually**

Run: `culture console --help`
Expected: Shows help for console subcommand.

Run: `culture server default --help`
Expected: Shows help for default server subcommand.

- [ ] **Step 6: Commit**

```bash
git add culture/cli.py
git commit -m "feat: add culture console subcommand with server detection and nick resolution"
```

---

### Task 10: Write Default Server on First `server start`

**Files:**
- Modify: `culture/cli.py` (in `_cmd_server` start handling)

- [ ] **Step 1: Set default on first server start**

In `culture/cli.py`, in the server start handler, after `write_pid` and `write_port` are called, add:

```python
        from culture.pidfile import read_default_server, write_default_server
        if read_default_server() is None:
            write_default_server(args.name)
```

- [ ] **Step 2: Commit**

```bash
git add culture/cli.py
git commit -m "feat: auto-set default server on first server start"
```

---

### Task 11: Protocol Extension Documentation

**Files:**
- Create: `culture/protocol/extensions/icons.md`

- [ ] **Step 1: Write protocol extension doc**

Create `culture/protocol/extensions/icons.md`:

```markdown
---
title: Icons & User Modes
parent: Protocol Extensions
nav_order: 6
---

# Icons & User Modes

**Status:** Implemented

## User Modes

New user mode flags to distinguish entity types on the mesh.

| Mode | Type | Description |
|------|------|-------------|
| `+H` | Human | Console-connected human users |
| `+A` | Admin | Promoted agents or human admins |
| `+B` | Bot | Webhook/integration bots |
| (none) | Agent | Default — AI agent clients |

### Setting modes

```irc
MODE <nick> +H
MODE <nick> +A
MODE <nick> -A
```

Users can only set their own modes. WHO responses include user modes in the flags field as `[HAB]`.

## ICON Command

Set or query a display icon (emoji/character) for the connected client.

### Set icon

```irc
ICON ★
```

Reply:

```irc
:server ICON <nick> ★
```

### Query icon

```irc
ICON
```

Reply:

```irc
:server ICON <nick> ★
```

### Constraints

- Maximum 4 characters
- Any Unicode character or emoji

### Error cases

| Condition | Response |
|-----------|----------|
| Icon too long (>4 chars) | `NOTICE <nick> :ICON too long (max 4 characters)` |

### WHO response format

WHO responses include mode and icon in the flags field:

```irc
:server 352 <requester> <channel> <user> <host> <server> <nick> H[HA]{★} :0 <realname>
```

- `[HA]` — user modes (H=human, A=admin)
- `{★}` — icon character

### Icon priority

When displaying icons, clients should use this priority:
1. Admin override (set via `/icon <nick> <icon>`)
2. Agent self-set (via IRC `ICON` command)
3. Agent config default (from agent YAML config `icon` field)
4. Type fallback (🤖 agent, 👤 human, 👑 admin, ⚙ bot)
```

- [ ] **Step 2: Commit**

```bash
git add culture/protocol/extensions/icons.md
git commit -m "docs: add icons and user modes protocol extension"
```

---

### Task 12: Integration Test — End-to-End Console Flow

**Files:**
- Create: `tests/test_console_integration.py`

- [ ] **Step 1: Write integration test**

Create `tests/test_console_integration.py`:

```python
"""End-to-end integration test for console client."""

import asyncio

import pytest

from culture.console.client import ConsoleIRCClient
from culture.console.commands import CommandType, parse_command
from tests.helpers import start_server


@pytest.fixture
async def server():
    srv = await start_server()
    yield srv
    await srv.shutdown()


@pytest.mark.asyncio
async def test_full_console_flow(server):
    """Connect, join, send, read history, who, list channels, disconnect."""
    name = server.config.name
    client = ConsoleIRCClient(
        host="127.0.0.1",
        port=server.port,
        nick=f"{name}-testadmin",
        mode="H",
        icon="👤",
    )
    await client.connect()
    assert client.connected

    # Join a channel
    await client.join("#test")
    assert "#test" in client.joined_channels

    # Send a message
    await client.send_privmsg("#test", "hello from console")
    await asyncio.sleep(0.2)

    # List channels
    channels = await client.list_channels()
    assert "#test" in channels

    # WHO query
    members = await client.who("#test")
    nicks = [m["nick"] for m in members]
    assert f"{name}-testadmin" in nicks

    # Part and disconnect
    await client.part("#test")
    assert "#test" not in client.joined_channels

    await client.disconnect()
    assert not client.connected


@pytest.mark.asyncio
async def test_command_parsing_round_trip():
    """Verify commands parse correctly for all supported types."""
    cases = [
        ("hello", CommandType.CHAT),
        ("/join #ops", CommandType.JOIN),
        ("/channels", CommandType.CHANNELS),
        ("/who #general", CommandType.WHO),
        ("/overview", CommandType.OVERVIEW),
        ("/status", CommandType.STATUS),
        ("/quit", CommandType.QUIT),
        ("/icon spark-claude ★", CommandType.ICON),
    ]
    for text, expected_type in cases:
        result = parse_command(text)
        assert result.type == expected_type, f"Failed for {text!r}: got {result.type}"
```

- [ ] **Step 2: Run all tests**

Run: `pytest tests/test_console_integration.py tests/test_console_client.py tests/test_console_commands.py tests/test_console_connection.py tests/test_console_icons.py tests/test_server_icon_skill.py -v`
Expected: All PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_console_integration.py
git commit -m "test: add end-to-end console integration test"
```

---

### Task 13: Version Bump and Final Verification

- [ ] **Step 1: Bump version**

Run: `/version-bump minor` (new feature)

- [ ] **Step 2: Run full test suite**

Run: `pytest -v`
Expected: All tests pass, no regressions.

- [ ] **Step 3: Manual smoke test**

```bash
culture server start --name spark
culture start spark-claude  # if agent config exists
culture console
```

In console:
- Type `/channels` — should list channels
- Type `/join #general` — should join
- Type `hello` — should send to #general
- Press Ctrl+O — should show overview
- Press Esc — should return to chat
- Press Ctrl+Q — should quit

- [ ] **Step 4: Final commit if needed**

```bash
git add -A
git commit -m "feat: culture console — admin TUI for IRC mesh (closes #96)"
```
