# tests/test_persistence.py
"""Tests for platform-specific auto-start service generation."""

import sys
from unittest.mock import patch

import pytest

from agentirc.persistence import (
    get_platform,
    _build_systemd_unit,
    _build_launchd_plist,
    _build_windows_bat,
    install_service,
    list_services,
)


def test_get_platform_linux():
    with patch.object(sys, "platform", "linux"):
        assert get_platform() == "linux"


def test_get_platform_macos():
    with patch.object(sys, "platform", "darwin"):
        assert get_platform() == "macos"


def test_get_platform_windows():
    with patch.object(sys, "platform", "win32"):
        assert get_platform() == "windows"


def test_build_systemd_unit():
    unit = _build_systemd_unit(
        name="agentirc-server-spark",
        command=["agentirc", "server", "start", "--foreground", "--name", "spark"],
        description="agentirc server spark",
    )
    assert "[Unit]" in unit
    assert "Description=agentirc server spark" in unit
    assert "ExecStart=agentirc server start --foreground --name spark" in unit
    assert "Restart=on-failure" in unit
    assert "WantedBy=default.target" in unit


def test_build_launchd_plist():
    plist = _build_launchd_plist(
        name="com.agentirc.server-spark",
        command=["agentirc", "server", "start", "--foreground", "--name", "spark"],
        description="agentirc server spark",
    )
    assert "<key>Label</key>" in plist
    assert "com.agentirc.server-spark" in plist
    assert "<string>agentirc</string>" in plist
    assert "<key>KeepAlive</key>" in plist
    assert "<true/>" in plist


def test_build_windows_bat():
    bat = _build_windows_bat(
        command=["agentirc", "server", "start", "--foreground", "--name", "spark"],
    )
    assert ":loop" in bat
    assert "agentirc server start --foreground --name spark" in bat
    assert "if %ERRORLEVEL% EQU 0 goto end" in bat
    assert "timeout /t 5" in bat
    assert "goto loop" in bat
    assert ":end" in bat


def test_install_service_linux(tmp_path):
    """Install writes a systemd unit file and returns its path."""
    unit_dir = tmp_path / "systemd" / "user"
    with patch("agentirc.persistence.get_platform", return_value="linux"), \
         patch("agentirc.persistence._systemd_user_dir", return_value=unit_dir), \
         patch("agentirc.persistence._run_cmd"):
        path = install_service(
            "agentirc-server-spark",
            ["agentirc", "server", "start", "--foreground", "--name", "spark"],
            "agentirc server spark",
        )
    assert path.exists()
    assert path.name == "agentirc-server-spark.service"
    content = path.read_text()
    assert "ExecStart=" in content


def test_list_services_linux(tmp_path):
    """list_services returns installed service names."""
    unit_dir = tmp_path / "systemd" / "user"
    unit_dir.mkdir(parents=True)
    (unit_dir / "agentirc-server-spark.service").write_text("[Unit]\n")
    (unit_dir / "agentirc-agent-spark-claude.service").write_text("[Unit]\n")
    (unit_dir / "unrelated.service").write_text("[Unit]\n")

    with patch("agentirc.persistence.get_platform", return_value="linux"), \
         patch("agentirc.persistence._systemd_user_dir", return_value=unit_dir):
        services = list_services()

    assert "agentirc-server-spark" in services
    assert "agentirc-agent-spark-claude" in services
    assert "unrelated" not in services
