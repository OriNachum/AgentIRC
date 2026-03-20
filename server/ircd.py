# server/ircd.py
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from server.config import ServerConfig
from server.channel import Channel
from server.skill import Event, Skill

if TYPE_CHECKING:
    from server.client import Client


class IRCd:
    """The agentirc IRC server."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.clients: dict[str, Client] = {}  # nick -> Client
        self.channels: dict[str, Channel] = {}  # name -> Channel
        self.skills: list[Skill] = []
        self._server: asyncio.Server | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_connection,
            self.config.host,
            self.config.port,
        )

    async def register_skill(self, skill: Skill) -> None:
        self.skills.append(skill)
        await skill.start(self)

    async def emit_event(self, event: Event) -> None:
        for skill in self.skills:
            await skill.on_event(event)

    def get_skill_for_command(self, command: str) -> Skill | None:
        for skill in self.skills:
            if command in skill.commands:
                return skill
        return None

    async def stop(self) -> None:
        for skill in self.skills:
            await skill.stop()
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        from server.client import Client

        client = Client(reader, writer, self)
        try:
            await client.handle()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            self._remove_client(client)
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionError, BrokenPipeError):
                pass

    def _remove_client(self, client: Client) -> None:
        if client.nick and client.nick in self.clients:
            del self.clients[client.nick]
        for channel in list(client.channels):
            channel.remove(client)
            if not channel.members:
                del self.channels[channel.name]

    def get_or_create_channel(self, name: str) -> Channel:
        if name not in self.channels:
            self.channels[name] = Channel(name)
        return self.channels[name]
