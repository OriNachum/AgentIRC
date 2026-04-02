# tests/test_mesh_config.py
"""Tests for mesh.yaml configuration module."""

import pytest

from agentirc.mesh_config import (
    MeshConfig,
    MeshServerConfig,
    MeshLinkConfig,
    MeshAgentConfig,
    load_mesh_config,
    save_mesh_config,
)


def test_mesh_config_round_trip(tmp_path):
    """Save and reload a mesh config — all fields preserved."""
    config = MeshConfig(
        server=MeshServerConfig(
            name="spark",
            host="0.0.0.0",
            port=6667,
            links=[
                MeshLinkConfig(name="thor", host="192.168.1.12", port=6667, password="secret", trust="full"),
            ],
        ),
        agents=[
            MeshAgentConfig(nick="claude", type="claude", workdir="~/projects/myproject", channels=["#general"]),
            MeshAgentConfig(nick="codex", type="codex", workdir="~/projects/other", channels=["#general", "#dev"]),
        ],
    )

    path = tmp_path / "mesh.yaml"
    save_mesh_config(config, path)
    loaded = load_mesh_config(path)

    assert loaded.server.name == "spark"
    assert loaded.server.port == 6667
    assert len(loaded.server.links) == 1
    assert loaded.server.links[0].name == "thor"
    assert loaded.server.links[0].password == "secret"
    assert loaded.server.links[0].trust == "full"
    assert len(loaded.agents) == 2
    assert loaded.agents[0].nick == "claude"
    assert loaded.agents[0].type == "claude"
    assert loaded.agents[0].workdir == "~/projects/myproject"
    assert loaded.agents[1].nick == "codex"
    assert loaded.agents[1].channels == ["#general", "#dev"]


def test_mesh_config_defaults(tmp_path):
    """Minimal config uses sensible defaults."""
    config = MeshConfig(
        server=MeshServerConfig(name="test"),
    )
    path = tmp_path / "mesh.yaml"
    save_mesh_config(config, path)
    loaded = load_mesh_config(path)

    assert loaded.server.name == "test"
    assert loaded.server.host == "0.0.0.0"
    assert loaded.server.port == 6667
    assert loaded.server.links == []
    assert loaded.agents == []


def test_mesh_config_empty_password(tmp_path):
    """Empty password is preserved (signals 'prompt during setup')."""
    config = MeshConfig(
        server=MeshServerConfig(
            name="spark",
            links=[MeshLinkConfig(name="thor", host="1.2.3.4", port=6667, password="")],
        ),
    )
    path = tmp_path / "mesh.yaml"
    save_mesh_config(config, path)
    loaded = load_mesh_config(path)

    assert loaded.server.links[0].password == ""


def test_mesh_config_file_not_found():
    """Loading a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_mesh_config("/nonexistent/mesh.yaml")
