"""Tests for overview web renderer."""
import os
import signal
import threading
import time

from agentirc.overview.model import Agent, Message, MeshState, Room
from agentirc.overview.renderer_web import render_html, serve_web, _stop_existing_overview
from agentirc import pidfile


def _make_fixture() -> MeshState:
    now = time.time()
    agent = Agent(
        nick="spark-claude", status="active", activity="working on: tests",
        channels=["#general"], server="spark",
        backend="claude", model="claude-opus-4-6",
    )
    msg = Message(nick="spark-claude", text="hello", timestamp=now - 60, channel="#general")
    room = Room(
        name="#general", topic="Testing",
        members=[agent], operators=["spark-claude"],
        federation_servers=[], messages=[msg],
    )
    return MeshState(server_name="spark", rooms=[room], agents=[agent], federation_links=[])


def test_render_html_produces_valid_html():
    mesh = _make_fixture()
    html = render_html(mesh, message_limit=4)
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html


def test_render_html_contains_content():
    mesh = _make_fixture()
    html = render_html(mesh, message_limit=4)
    assert "spark mesh" in html
    assert "#general" in html
    assert "spark-claude" in html
    assert "hello" in html


def test_render_html_has_cream_styles():
    mesh = _make_fixture()
    html = render_html(mesh, message_limit=4)
    assert "#faf7f2" in html or "faf7f2" in html


def test_render_html_has_auto_refresh():
    mesh = _make_fixture()
    html = render_html(mesh, message_limit=4, refresh_interval=5)
    assert 'http-equiv="refresh"' in html or "refresh" in html.lower()


def test_render_html_has_table_elements():
    mesh = _make_fixture()
    html = render_html(mesh, message_limit=4)
    assert "<table" in html
    assert "<th>" in html or "<th " in html
    assert "status-active" in html


# --- serve_web PID/port management tests ---


def test_serve_web_writes_and_cleans_pid_port(tmp_path, monkeypatch):
    """serve_web writes PID and port files, cleans up on shutdown."""
    monkeypatch.setattr(pidfile, "PID_DIR", str(tmp_path))

    pid_name = "overview-testserver"
    pid_path = tmp_path / f"{pid_name}.pid"
    port_path = tmp_path / f"{pid_name}.port"

    # We need to stop the server after it starts. Patch HTTPServer to
    # capture the instance so we can call shutdown() from a timer.
    from http.server import HTTPServer
    captured = {}
    _orig_init = HTTPServer.__init__

    def _patched_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        captured["httpd"] = self

    monkeypatch.setattr(HTTPServer, "__init__", _patched_init)

    def _run():
        serve_web(
            host="127.0.0.1", port=6667, server_name="testserver",
            serve_port=0,
        )

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    # Wait for PID file to appear
    for _ in range(40):
        if pid_path.exists() and port_path.exists():
            break
        time.sleep(0.05)

    assert pid_path.exists(), "PID file should be created"
    assert port_path.exists(), "Port file should be created"

    stored_pid = int(pid_path.read_text().strip())
    stored_port = int(port_path.read_text().strip())
    assert stored_pid == os.getpid()
    assert stored_port > 0

    # Shut down the server gracefully
    captured["httpd"].shutdown()
    t.join(timeout=5)

    assert not pid_path.exists(), "PID file should be cleaned up"
    assert not port_path.exists(), "Port file should be cleaned up"


def test_stop_existing_overview_kills_previous(tmp_path, monkeypatch):
    """_stop_existing_overview sends SIGTERM to an existing instance."""
    monkeypatch.setattr(pidfile, "PID_DIR", str(tmp_path))

    pid_name = "overview-testserver"
    # Write fake PID/port files
    (tmp_path / f"{pid_name}.pid").write_text("99999")
    (tmp_path / f"{pid_name}.port").write_text("12345")

    killed_pids = []
    monkeypatch.setattr(pidfile, "is_process_alive", lambda pid: False)
    monkeypatch.setattr(os, "kill", lambda pid, sig: killed_pids.append((pid, sig)))

    # Patch is_process_alive in the renderer_web module too
    import agentirc.overview.renderer_web as rweb
    monkeypatch.setattr(rweb, "is_process_alive", lambda pid: False)

    _stop_existing_overview(pid_name)

    # Files should be cleaned up (stale PID — process not alive)
    assert not (tmp_path / f"{pid_name}.pid").exists()
    assert not (tmp_path / f"{pid_name}.port").exists()


def test_stop_existing_overview_cleans_stale_pid(tmp_path, monkeypatch):
    """Stale PID files (dead process) are cleaned without sending signals."""
    monkeypatch.setattr(pidfile, "PID_DIR", str(tmp_path))

    pid_name = "overview-stale"
    (tmp_path / f"{pid_name}.pid").write_text("11111")
    (tmp_path / f"{pid_name}.port").write_text("9999")

    kills = []
    monkeypatch.setattr(os, "kill", lambda pid, sig: kills.append((pid, sig)))

    import agentirc.overview.renderer_web as rweb
    monkeypatch.setattr(rweb, "is_process_alive", lambda pid: False)

    _stop_existing_overview(pid_name)

    assert not (tmp_path / f"{pid_name}.pid").exists()
    assert not (tmp_path / f"{pid_name}.port").exists()
    assert kills == [], "No signals should be sent for a dead process"
