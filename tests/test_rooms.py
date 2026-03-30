"""Tests for rooms management."""
import pytest


def test_channel_has_room_metadata_fields():
    """Channel should have room metadata fields, all None/empty by default."""
    from agentirc.server.channel import Channel

    ch = Channel("#test")
    assert ch.room_id is None
    assert ch.creator is None
    assert ch.owner is None
    assert ch.purpose is None
    assert ch.instructions is None
    assert ch.tags == []
    assert ch.persistent is False
    assert ch.agent_limit is None
    assert ch.extra_meta == {}
    assert ch.archived is False
    assert ch.created_at is None


def test_channel_is_managed():
    """Channel with room_id is considered managed."""
    from agentirc.server.channel import Channel

    ch = Channel("#test")
    assert ch.is_managed is False
    ch.room_id = "R7K2M9"
    assert ch.is_managed is True


def test_generate_room_id_format():
    """Room ID starts with R followed by uppercase alphanumeric."""
    from agentirc.server.rooms_util import generate_room_id
    import re

    rid = generate_room_id()
    assert rid.startswith("R")
    assert len(rid) >= 6
    assert re.match(r"^R[0-9A-Z]+$", rid)


def test_generate_room_id_uniqueness():
    """Two consecutive calls produce different IDs."""
    from agentirc.server.rooms_util import generate_room_id

    ids = {generate_room_id() for _ in range(100)}
    assert len(ids) == 100


def test_parse_room_meta_basic():
    """Parse key=value pairs separated by semicolons."""
    from agentirc.server.rooms_util import parse_room_meta

    meta = parse_room_meta("purpose=Help with Python;tags=python,code-help;persistent=true")
    assert meta["purpose"] == "Help with Python"
    assert meta["tags"] == "python,code-help"
    assert meta["persistent"] == "true"


def test_parse_room_meta_instructions_last():
    """Instructions field is always last and may contain semicolons."""
    from agentirc.server.rooms_util import parse_room_meta

    meta = parse_room_meta(
        "purpose=Help;tags=py;instructions=Do this; then that; finally done"
    )
    assert meta["purpose"] == "Help"
    assert meta["tags"] == "py"
    assert meta["instructions"] == "Do this; then that; finally done"


def test_parse_room_meta_empty():
    """Empty string returns empty dict."""
    from agentirc.server.rooms_util import parse_room_meta

    assert parse_room_meta("") == {}


@pytest.mark.asyncio
async def test_roomcreate_basic(server, make_client):
    """ROOMCREATE creates a managed room and returns room ID."""
    alice = await make_client(nick="testserv-alice", user="alice")
    await alice.send(
        "ROOMCREATE #pyhelp :purpose=Python help;tags=python,code-help;persistent=true"
    )
    lines = await alice.recv_all(timeout=1.0)
    joined = " ".join(lines)

    # Should get a ROOMCREATED response with room ID
    assert "ROOMCREATED" in joined
    assert "#pyhelp" in joined
    assert " R" in joined  # room ID starts with R

    # Should have auto-joined the channel
    assert "JOIN" in joined
    assert "353" in joined  # RPL_NAMREPLY


@pytest.mark.asyncio
async def test_roomcreate_stores_metadata(server, make_client):
    """ROOMCREATE stores metadata on the channel."""
    alice = await make_client(nick="testserv-alice", user="alice")
    await alice.send(
        "ROOMCREATE #pyhelp :purpose=Python help;tags=python,code-help;persistent=true;agent_limit=5"
    )
    await alice.recv_all(timeout=1.0)

    channel = server.channels.get("#pyhelp")
    assert channel is not None
    assert channel.is_managed
    assert channel.room_id is not None
    assert channel.room_id.startswith("R")
    assert channel.creator == "testserv-alice"
    assert channel.owner == "testserv-alice"
    assert channel.purpose == "Python help"
    assert channel.tags == ["python", "code-help"]
    assert channel.persistent is True
    assert channel.agent_limit == 5
    assert channel.created_at is not None


@pytest.mark.asyncio
async def test_roomcreate_with_instructions(server, make_client):
    """ROOMCREATE handles instructions field (may contain semicolons)."""
    alice = await make_client(nick="testserv-alice", user="alice")
    await alice.send(
        "ROOMCREATE #help :purpose=Help;tags=py;instructions=Do this; then that; done"
    )
    await alice.recv_all(timeout=1.0)

    channel = server.channels["#help"]
    assert channel.instructions == "Do this; then that; done"


@pytest.mark.asyncio
async def test_roomcreate_duplicate_name(server, make_client):
    """ROOMCREATE on existing channel fails."""
    alice = await make_client(nick="testserv-alice", user="alice")
    await alice.send("ROOMCREATE #pyhelp :purpose=first")
    await alice.recv_all(timeout=1.0)

    await alice.send("ROOMCREATE #pyhelp :purpose=second")
    lines = await alice.recv_all(timeout=1.0)
    joined = " ".join(lines)
    assert "already exists" in joined.lower() or "403" in joined


@pytest.mark.asyncio
async def test_roomcreate_requires_hash(server, make_client):
    """ROOMCREATE requires channel name starting with #."""
    alice = await make_client(nick="testserv-alice", user="alice")
    await alice.send("ROOMCREATE badname :purpose=test")
    lines = await alice.recv_all(timeout=1.0)
    assert "badname" not in server.channels


@pytest.mark.asyncio
async def test_roomcreate_no_params(server, make_client):
    """ROOMCREATE with missing params returns error."""
    alice = await make_client(nick="testserv-alice", user="alice")
    await alice.send("ROOMCREATE")
    resp = await alice.recv()
    assert "461" in resp  # ERR_NEEDMOREPARAMS


@pytest.mark.asyncio
async def test_client_tags_default_empty(server, make_client):
    """Client tags default to empty list."""
    alice = await make_client(nick="testserv-alice", user="alice")
    client = server.clients["testserv-alice"]
    assert client.tags == []
