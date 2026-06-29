"""Public API for launching the Fleet Dashboard."""

from __future__ import annotations

import threading
from pathlib import Path

from subagent_fleet.cli import _load_or_exit


def launch_dashboard(config_path: Path, port: int = 8080) -> None:
    """Launch the Fleet Dashboard web server.

    Args:
        config_path: Path to fleet.yaml configuration file.
        port: Port to bind the dashboard server (default: 8080).

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
        )
    except Exception as exc:
        console.print(f"[red]Failed to start dashboard:[/red]\n{exc}")
        raise SystemExit(1) from exc

    # Run the server in a daemon thread so Ctrl+C can shut it down cleanly.
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    console.print(f"[bold blue]Dashboard running on http://127.0.0.1:{port}[/bold blue]")
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
