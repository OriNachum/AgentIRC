"""PID file management for agentirc daemon instances."""

from __future__ import annotations

import os
from pathlib import Path

PID_DIR = os.path.expanduser("~/.agentirc/pids")


def write_pid(name: str, pid: int) -> Path:
    """Write a PID file for the named daemon. Creates the directory if needed."""
    pid_dir = Path(PID_DIR)
    pid_dir.mkdir(parents=True, exist_ok=True)
    pid_path = pid_dir / f"{name}.pid"
    pid_path.write_text(str(pid))
    return pid_path


def read_pid(name: str) -> int | None:
    """Read the PID for the named daemon. Returns None if file is missing."""
    pid_path = Path(PID_DIR) / f"{name}.pid"
    if not pid_path.exists():
        return None
    try:
        return int(pid_path.read_text().strip())
    except (ValueError, OSError):
        return None


def remove_pid(name: str) -> None:
    """Remove the PID file for the named daemon if it exists."""
    pid_path = Path(PID_DIR) / f"{name}.pid"
    try:
        pid_path.unlink()
    except FileNotFoundError:
        pass


def write_port(name: str, port: int) -> Path:
    """Write a port file for the named daemon. Creates the directory if needed."""
    pid_dir = Path(PID_DIR)
    pid_dir.mkdir(parents=True, exist_ok=True)
    port_path = pid_dir / f"{name}.port"
    port_path.write_text(str(port))
    return port_path


def read_port(name: str) -> int | None:
    """Read the port for the named daemon. Returns None if file is missing."""
    port_path = Path(PID_DIR) / f"{name}.port"
    if not port_path.exists():
        return None
    try:
        return int(port_path.read_text().strip())
    except (ValueError, OSError):
        return None


def remove_port(name: str) -> None:
    """Remove the port file for the named daemon if it exists."""
    port_path = Path(PID_DIR) / f"{name}.port"
    try:
        port_path.unlink()
    except FileNotFoundError:
        pass


def is_process_alive(pid: int) -> bool:
    """Check whether a process with the given PID is alive."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we don't have permission to signal it
        return True
