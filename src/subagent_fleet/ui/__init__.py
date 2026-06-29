"""Public API for launching the Fleet Dashboard."""

from __future__ import annotations

import json
import threading
from pathlib import Path


def launch_dashboard(
    config_path: Path,
    port: int = 8080,
    log_path: str | None = None,
) -> None:
    """Launch the Fleet Dashboard web server.

    Args:
        config_path: Path to fleet.yaml configuration file.
        port: Port to bind the dashboard server (default: 8080).
        log_path: Optional path to a LiteLLM debug log for trace streaming.

    Raises:
        SystemExit: If the config is invalid or the server fails to start.
    """
    from subagent_fleet.cli import console

    fleet = _load_or_exit(config_path)

    try:
        from subagent_fleet.ui.server import DashboardServer

        server = DashboardServer(
            fleet_config=fleet,
            host="127.0.0.1",
            port=port,
            log_path=log_path,
        )
    except Exception as exc:
        console.print(f"[red]Failed to start dashboard:[/red]\n{exc}")
        raise SystemExit(1) from exc

    # Run the server in a daemon thread so Ctrl+C can shut it down cleanly.
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    console.print(f"[bold blue]Dashboard running on http://127.0.0.1:{port}[/bold blue]")
    if log_path:
        console.print(f"[dim]Trace stream: tailing {log_path}[/dim]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]")

    try:
        # Block the main thread until Ctrl+C is pressed.
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold]Stopping dashboard...[/bold]")
        server.shutdown()
        server_thread.join(timeout=2)


def _load_or_exit(path: Path):
    """Load fleet config or exit with an error message."""
    from subagent_fleet.cli import console
    from subagent_fleet.config import ConfigError, load_config

    try:
        return load_config(path)
    except ConfigError as exc:
        console.print(f"[red]Invalid {path}:[/red]\n\n{exc}")
        raise SystemExit(1) from exc


def emit_warmup_event(
    dashboard_url: str = "http://127.0.0.1:8080",
    model_name: str = "",
    node_name: str = "",
    status: str = "pending",
) -> None:
    """Emit a warmup-progress SSE event to a running dashboard.

    This is intended for use by the ``warmup`` CLI command so that users
    watching the dashboard see live progress without polling.

    Args:
        dashboard_url: Base URL of the running dashboard server.
        model_name: Name of the model being warmed up.
        node_name: Name of the Ollama node.
        status: One of "pending", "ok", or "error: <reason>".
    """
    import urllib.request

    payload = {
        "model_name": model_name,
        "node_name": node_name,
        "status": status,
    }
    url = f"{dashboard_url.rstrip('/')}/api/warmup-progress"
    data = f"data: {json.dumps(payload)}\n\n".encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "text/event-stream")
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            resp.read()
    except Exception:
        pass  # Dashboard not running — that's fine.
