"""Render mesh overview as HTML and serve via HTTP."""
from __future__ import annotations

import atexit
import asyncio
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
from pathlib import Path
import signal
import threading
import time

import re

import mistune

from agentirc.pidfile import (
    is_process_alive, read_pid, read_port,
    remove_pid, remove_port, write_pid, write_port,
)
from .collector import collect_mesh_state
from .model import MeshState
from .renderer_text import render_text


def _create_markdown() -> mistune.Markdown:
    """Create a mistune renderer that escapes raw HTML in input."""
    return mistune.create_markdown(escape=True, plugins=['table'])


def _load_css() -> str:
    """Load the cream stylesheet."""
    css_path = Path(__file__).parent / "web" / "style.css"
    return css_path.read_text()


def _inject_status_badges(html: str) -> str:
    """Replace status text in table cells with styled badges."""
    for status in ("active", "idle", "paused", "remote"):
        html = re.sub(
            rf"(<td>)\s*{status}\s*(</td>)",
            rf'\1<span class="status-{status}">{status}</span>\2',
            html,
        )
    return html


def render_html(
    mesh: MeshState,
    *,
    room_filter: str | None = None,
    agent_filter: str | None = None,
    message_limit: int = 4,
    refresh_interval: int = 5,
) -> str:
    """Render MeshState as a full HTML page."""
    md_text = render_text(
        mesh,
        room_filter=room_filter,
        agent_filter=agent_filter,
        message_limit=message_limit,
    )
    md = _create_markdown()
    body_html = md(md_text)
    body_html = _inject_status_badges(body_html)
    css = _load_css()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="{refresh_interval}">
    <title>agentirc overview</title>
    <style>{css}</style>
</head>
<body>
    <div class="refresh-indicator">live &mdash; refreshing every {refresh_interval}s</div>
    {body_html}
</body>
</html>"""


def _stop_existing_overview(pid_name: str) -> None:
    """Kill a previous overview instance if running, clean up its files."""
    existing_pid = read_pid(pid_name)
    if existing_pid and is_process_alive(existing_pid):
        existing_port = read_port(pid_name)
        os.kill(existing_pid, signal.SIGTERM)
        for _ in range(20):
            if not is_process_alive(existing_pid):
                break
            time.sleep(0.1)
        else:
            try:
                os.kill(existing_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        remove_pid(pid_name)
        remove_port(pid_name)
        port_msg = f", port {existing_port}" if existing_port else ""
        print(
            f"Stopped previous overview for '{pid_name.removeprefix('overview-')}'"
            f" (PID {existing_pid}{port_msg})",
            flush=True,
        )
    elif existing_pid:
        remove_pid(pid_name)
        remove_port(pid_name)


def serve_web(
    host: str,
    port: int,
    server_name: str,
    *,
    room_filter: str | None = None,
    agent_filter: str | None = None,
    message_limit: int = 4,
    refresh_interval: int = 5,
    serve_port: int = 0,
) -> None:
    """Start a local HTTP server serving the live overview."""
    pid_name = f"overview-{server_name}"
    _stop_existing_overview(pid_name)

    class OverviewHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            mesh = asyncio.run(collect_mesh_state(
                host=host, port=port, server_name=server_name,
                message_limit=message_limit,
            ))
            html = render_html(
                mesh,
                room_filter=room_filter,
                agent_filter=agent_filter,
                message_limit=message_limit,
                refresh_interval=refresh_interval,
            )
            content = html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, format, *args):
            pass  # Suppress request logging

    httpd = HTTPServer(("127.0.0.1", serve_port), OverviewHandler)
    actual_port = httpd.server_address[1]

    write_pid(pid_name, os.getpid())
    write_port(pid_name, actual_port)

    def _cleanup():
        remove_pid(pid_name)
        remove_port(pid_name)

    atexit.register(_cleanup)
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, lambda _sig, _frame: httpd.shutdown())

    print(f"Overview dashboard: http://localhost:{actual_port}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        httpd.server_close()
        _cleanup()
        atexit.unregister(_cleanup)
