"""Rooms management skill — ROOMCREATE, ROOMMETA, TAGS, ROOMINVITE, ROOMKICK, ROOMARCHIVE."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from agentirc.protocol.message import Message
from agentirc.protocol import replies
from agentirc.server.rooms_util import generate_room_id, parse_room_meta
from agentirc.server.skill import Event, EventType, Skill

if TYPE_CHECKING:
    from agentirc.server.client import Client


class RoomsSkill(Skill):
    name = "rooms"
    commands = {"ROOMCREATE", "ROOMMETA", "TAGS", "ROOMINVITE", "ROOMKICK", "ROOMARCHIVE"}

    async def on_command(self, client: Client, msg: Message) -> None:
        handler = {
            "ROOMCREATE": self._handle_roomcreate,
            "ROOMMETA": self._handle_roommeta,
            "TAGS": self._handle_tags,
            "ROOMINVITE": self._handle_roominvite,
            "ROOMKICK": self._handle_roomkick,
            "ROOMARCHIVE": self._handle_roomarchive,
        }.get(msg.command)
        if handler:
            await handler(client, msg)

    async def _handle_roomcreate(self, client: Client, msg: Message) -> None:
        if len(msg.params) < 2:
            await client.send_numeric(
                replies.ERR_NEEDMOREPARAMS, "ROOMCREATE", "Not enough parameters"
            )
            return

        channel_name = msg.params[0]
        if not channel_name.startswith("#"):
            await client.send(Message(
                prefix=self.server.config.name,
                command="NOTICE",
                params=[client.nick, "Channel name must start with #"],
            ))
            return

        if channel_name in self.server.channels:
            await client.send_numeric(
                replies.ERR_NOSUCHCHANNEL, channel_name, "Channel already exists"
            )
            return

        meta_text = msg.params[1]
        meta = parse_room_meta(meta_text)

        channel = self.server.get_or_create_channel(channel_name)
        channel.room_id = generate_room_id()
        channel.creator = client.nick
        channel.owner = client.nick
        channel.purpose = meta.get("purpose")
        channel.instructions = meta.get("instructions")
        channel.persistent = meta.get("persistent", "").lower() == "true"
        channel.created_at = time.time()
        channel.extra_meta = {}

        # Parse tags
        tags_str = meta.get("tags", "")
        channel.tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        # Parse agent_limit
        limit_str = meta.get("agent_limit")
        if limit_str:
            try:
                channel.agent_limit = int(limit_str)
            except ValueError:
                pass

        # Store extra metadata (anything not a known key)
        known_keys = {"purpose", "instructions", "persistent", "tags", "agent_limit"}
        for key, value in meta.items():
            if key not in known_keys:
                channel.extra_meta[key] = value

        # Auto-join creator as operator
        channel.add(client)
        client.channels.add(channel)

        # Send JOIN to the creator
        join_msg = Message(prefix=client.prefix, command="JOIN", params=[channel_name])
        await client.send(join_msg)

        # Send NAMES list
        nicks = " ".join(f"{channel.get_prefix(m)}{m.nick}" for m in channel.members)
        await client.send_numeric(replies.RPL_NAMREPLY, "=", channel_name, nicks)
        await client.send_numeric(replies.RPL_ENDOFNAMES, channel_name, "End of /NAMES list")

        # Send ROOMCREATED confirmation with room ID
        await client.send(Message(
            prefix=self.server.config.name,
            command="ROOMCREATED",
            params=[channel_name, channel.room_id, f"Room created: {channel.purpose or channel_name}"],
        ))

    async def _handle_roommeta(self, client: Client, msg: Message) -> None:
        pass  # Task 4

    async def _handle_tags(self, client: Client, msg: Message) -> None:
        pass  # Task 5

    async def _handle_roominvite(self, client: Client, msg: Message) -> None:
        pass  # Task 7

    async def _handle_roomkick(self, client: Client, msg: Message) -> None:
        pass  # Task 8

    async def _handle_roomarchive(self, client: Client, msg: Message) -> None:
        pass  # Task 9
