# ASSIMILAI: Replace BACKEND with your backend name (e.g., codex, opencode)
"""Generic agent daemon — template for new backends.

Copy this file into your backend directory and replace:
- _start_agent_runner() — wire up your agent's SDK/CLI
- _build_system_prompt() — customize the system prompt
- _on_mention() — customize how @mentions become prompts

Everything else (IRC transport, IPC, socket server, webhooks) works as-is.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

# These imports point to YOUR backend's copies of these files:
from agentirc.clients.BACKEND.config import DaemonConfig, AgentConfig
from agentirc.clients.BACKEND.ipc import make_response
from agentirc.clients.BACKEND.irc_transport import IRCTransport
from agentirc.clients.BACKEND.message_buffer import MessageBuffer
from agentirc.clients.BACKEND.socket_server import SocketServer
from agentirc.clients.BACKEND.webhook import WebhookClient, AlertEvent

logger = logging.getLogger(__name__)


class AgentDaemon:
    """Daemon that bridges an AI agent to the IRC network.

    This is the template. When assimilating into a new backend:
    1. Replace _start_agent_runner() with your agent's startup logic
    2. Replace _build_system_prompt() with your prompt format
    3. Adapt _on_mention() for your agent's prompt format
    """

    def __init__(self, config: DaemonConfig, agent: AgentConfig,
                 *, skip_agent: bool = False, socket_dir: str | None = None):
        self.config = config
        self.agent = agent
        self.skip_agent = skip_agent

        self._socket_path = os.path.join(
            socket_dir or os.environ.get("XDG_RUNTIME_DIR", "/tmp"),
            f"agentirc-{agent.nick}.sock",
        )

        self._transport: IRCTransport | None = None
        self._buffer: MessageBuffer | None = None
        self._socket_server: SocketServer | None = None
        self._webhook: WebhookClient | None = None
        self._stop_event: asyncio.Event | None = None

    def set_stop_event(self, event: asyncio.Event) -> None:
        """Register an external stop event for coordinated shutdown."""
        self._stop_event = event

    async def start(self) -> None:
        """Start all daemon components."""
        # 1. Message buffer
        self._buffer = MessageBuffer(max_per_channel=self.config.buffer_size)

        # 2. IRC transport
        self._transport = IRCTransport(
            host=self.config.server.host,
            port=self.config.server.port,
            nick=self.agent.nick,
            user=self.agent.nick,
            channels=list(self.agent.channels),
            buffer=self._buffer,
            on_mention=self._on_mention,
        )
        await self._transport.connect()

        # 3. Webhook client
        self._webhook = WebhookClient(
            config=self.config.webhooks,
            irc_send=self._transport.send_privmsg,
        )

        # 4. Unix socket server
        self._socket_server = SocketServer(
            path=self._socket_path,
            handler=self._handle_ipc,
        )
        await self._socket_server.start()

        # 5. Start agent runner (REPLACE THIS in your backend)
        if not self.skip_agent:
            await self._start_agent_runner()

    async def stop(self) -> None:
        """Stop all daemon components."""
        if self._socket_server:
            await self._socket_server.stop()
        if self._transport:
            await self._transport.disconnect()

    # ------------------------------------------------------------------
    # REPLACE THESE METHODS in your backend
    # ------------------------------------------------------------------

    async def _start_agent_runner(self) -> None:
        """Start the agent. REPLACE with your backend's agent startup."""
        raise NotImplementedError(
            "Replace _start_agent_runner() with your agent backend's startup logic. "
            "See agentirc/clients/claude/daemon.py for the Claude implementation."
        )

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent. REPLACE as needed."""
        return f"You are {self.agent.nick}, an AI agent on the agentirc IRC network."

    def _on_mention(self, target: str, sender: str, text: str) -> None:
        """Called when the agent is @mentioned. Sends prompt to runner."""
        prompt = f"[IRC @mention in {target}] <{sender}> {text}"
        # Queue the prompt to your agent runner here
        logger.info("@mention from %s in %s: %s", sender, target, text)

    # ------------------------------------------------------------------
    # IPC handler — works for all backends
    # ------------------------------------------------------------------

    async def _handle_ipc(self, msg: dict[str, Any]) -> dict[str, Any]:
        """Handle IPC requests from skill clients."""
        msg_type = msg.get("type", "")
        req_id = msg.get("id", "")

        if msg_type == "irc_send":
            channel = msg.get("channel", "")
            message = msg.get("message", "")
            if self._transport:
                await self._transport.send_privmsg(channel, message)
            return make_response(req_id, ok=True)

        elif msg_type == "irc_read":
            channel = msg.get("channel", "")
            limit = msg.get("limit", 50)
            if self._buffer:
                messages = self._buffer.read(channel, limit=limit)
                return make_response(req_id, ok=True, data={
                    "messages": [
                        {"nick": m.nick, "text": m.text, "timestamp": m.timestamp}
                        for m in messages
                    ]
                })
            return make_response(req_id, ok=False, error="No buffer")

        elif msg_type == "irc_ask":
            channel = msg.get("channel", "")
            message = msg.get("message", "")
            if self._transport and channel:
                await self._transport.send_privmsg(channel, message)
            if self._webhook:
                await self._webhook.fire(AlertEvent(
                    event_type="agent_question",
                    nick=self.agent.nick,
                    message=f"[QUESTION] [{self.agent.nick}] asked in {channel}: {message}",
                ))
            return make_response(req_id, ok=True)

        elif msg_type == "irc_join":
            channel = msg.get("channel", "")
            if self._transport:
                await self._transport.join_channel(channel)
            return make_response(req_id, ok=True)

        elif msg_type == "irc_part":
            channel = msg.get("channel", "")
            if self._transport:
                await self._transport.part_channel(channel)
            return make_response(req_id, ok=True)

        elif msg_type == "irc_who":
            target = msg.get("target", "")
            if self._transport:
                await self._transport.send_who(target)
            return make_response(req_id, ok=True)

        elif msg_type == "irc_channels":
            channels = self._transport.channels if self._transport else []
            return make_response(req_id, ok=True, data={"channels": channels})

        elif msg_type == "compact":
            # Send /compact to agent runner — ADAPT for your backend
            logger.info("IPC compact requested")
            return make_response(req_id, ok=True)

        elif msg_type == "clear":
            # Send /clear to agent runner — ADAPT for your backend
            logger.info("IPC clear requested")
            return make_response(req_id, ok=True)

        elif msg_type == "set_directory":
            path = msg.get("path", "")
            if not path:
                return make_response(req_id, ok=False, error="Missing 'path'")
            # Change agent working directory — ADAPT for your backend
            logger.info("IPC set_directory: %s", path)
            return make_response(req_id, ok=True)

        elif msg_type == "shutdown":
            if self._stop_event:
                self._stop_event.set()
            else:
                asyncio.create_task(self.stop())
            return make_response(req_id, ok=True)

        else:
            return make_response(req_id, ok=False, error=f"Unknown: {msg_type}")
