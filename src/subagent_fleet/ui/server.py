"""HTTP/SSE server for the Fleet Dashboard."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from subagent_fleet.config import FleetConfig
from subagent_fleet.discovery import discovery_to_json, discover_fleet
from subagent_fleet.status import get_agent_routes, routes_to_json


class DashboardServer(ThreadingHTTPServer):
    """HTTP server for the Fleet Dashboard.

    Serves:
        - /dashboard or / : HTML dashboard page
        - /api/status?include_loaded=true : JSON API with node status + agent routes
        - /static/* : Static assets (CSS, JS) in Phase 2+
        - /api/events : SSE endpoint for real-time updates (Phase 2+)

    Inherits ThreadingHTTPServer so each client connection gets its own thread.
    """

    def __init__(
        self,
        fleet_config: FleetConfig,
        host: str = "127.0.0.1",
        port: int = 8080,
        static_dir: Path | None = None,
    ) -> None:
        """Initialize the dashboard server.

        Args:
            fleet_config: Loaded FleetConfig from fleet.yaml.
            host: Host to bind to (default: 127.0.0.1 for localhost only).
            port: Port to bind to (default: 8080).
            static_dir: Optional directory containing static assets (CSS, JS).
        """
        super().__init__((host, port), DashboardRequestHandler)
        self.fleet_config = fleet_config
        self.static_dir = static_dir or Path(__file__).parent / "static"

    def serve_forever(self) -> None:
        """Start serving requests until shutdown is called."""
        super().serve_forever()


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Fleet Dashboard.

    Routes:
        - GET /dashboard or GET / : Serve HTML dashboard page
        - GET /api/status?include_loaded=true : Return JSON with node status + agent routes
        - GET /static/<file> : Serve static assets (CSS, JS)
        - GET /api/events : SSE endpoint for real-time updates (Phase 2+)
    """

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed_path = self.parse_request_path()

        if parsed_path == "/dashboard" or parsed_path == "/":
            self._serve_dashboard_page()
        elif parsed_path.startswith("/api/status"):
            include_loaded = self._parse_query_params().get("include_loaded", "false").lower() == "true"
            self._serve_status_json(include_loaded=include_loaded)
        elif parsed_path.startswith("/static/"):
            static_filename = parsed_path[len("/static/"):]
            self._serve_static_file(static_filename)
        elif parsed_path == "/api/events":
            # Phase 2+: SSE endpoint for real-time updates
            self._serve_sse()
        else:
            self.send_error(404, "Not Found")

    def do_HEAD(self) -> None:
        """Handle HEAD requests (health checks)."""
        parsed_path = self.parse_request_path()

        if parsed_path == "/dashboard" or parsed_path == "/" or parsed_path.startswith("/api/"):
            self.send_response(200, "OK")
            self.end_headers()
        else:
            self.send_error(404, "Not Found")

    def parse_request_path(self) -> str:
        """Parse the request path from the URL."""
        return self.path.split("?")[0]  # Strip query parameters

    def _parse_query_params(self) -> dict[str, str]:
        """Parse query parameters from the request URL."""
        from urllib.parse import parse_qs

        params = parse_qs(self.path.split("?", 1)[1]) if "?" in self.path else {}
        return {k: v[0] for k, v in params.items()}  # Flatten single-value params

    def _serve_dashboard_page(self) -> None:
        """Serve the HTML dashboard page."""
        # For MVP, serve a minimal inline HTML page. Phase 2+ will use templates/static files.
        html_content = self._generate_mvp_html()

        self.send_response(200, "OK")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def _generate_mvp_html(self) -> str:
        """Generate minimal MVP HTML dashboard with embedded CSS/JS."""
        # Load fleet config data for initial render
        nodes = discover_fleet(self.server.fleet_config, include_loaded=False)
        routes = get_agent_routes(self.server.fleet_config)

        # Serialize node data into HTML table rows
        node_rows_html = []
        for node in nodes:
            status_class = "status-online" if node.online else "status-offline"
            status_text = "Online" if node.online else "Offline"
            models_str = ", ".join(node.models) if node.models else "-"

            node_rows_html.append(f"""
                <tr>
                    <td>{node.name}</td>
                    <td><span class="{status_class}">{status_text}</span></td>
                    <td class="latency">{node.endpoint}</td>
                    <td class="models">{models_str}</td>
                </tr>""")

        # Serialize route data into HTML table rows
        route_rows_html = []
        for route in routes:
            route_rows_html.append(f"""
                <tr>
                    <td>{route.agent}</td>
                    <td>{route.node}</td>
                    <td>{route.ollama_model}</td>
                    <td class="latency">{route.litellm_alias}</td>
                </tr>""")

        # Build the full HTML document
        project_name = self.server.fleet_config.project.name
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fleet Dashboard - {project_name}</title>
    <style>
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --text-primary: #eaeaea;
            --text-secondary: #a0aec0;
            --accent-green: #48bb78;
            --accent-red: #f56565;
            --accent-yellow: #ecc94b;
            --border-color: #2d3748;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            padding: 2rem;
            line-height: 1.6;
        }}

        h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: var(--accent-green);
        }}

        .subtitle {{
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .card {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
        }}

        .card h2 {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}

        th, td {{
            text-align: left;
            padding: 0.75rem 0.5rem;
            border-bottom: 1px solid var(--border-color);
        }}

        th {{
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }}

        .status-online {{
            color: var(--accent-green);
        }}

        .status-offline {{
            color: var(--accent-red);
        }}

        .latency {{
            font-family: monospace;
            color: var(--text-secondary);
        }}

        .models {{
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}

        .empty-state {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
        }}
    </style>
</head>
<body>
    <h1>Fleet Dashboard</h1>
    <p class="subtitle">Project: {project_name}</p>

    <div class="grid">
        <!-- Node Health Panel -->
        <div class="card">
            <h2><span>&#x1f4cd;</span> Node Health</h2>
            {'<table>' if node_rows_html else '<div class="empty-state">No nodes configured</div>'}
            {"".join(node_rows_html)}
            </table>
        </div>

        <!-- Agent Routing Panel -->
        <div class="card">
            <h2><span>&#x1f517;</span> Agent Routing</h2>
            {'<table>' if route_rows_html else '<div class="empty-state">No agents configured</div>'}
            {"".join(route_rows_html)}
            </table>
        </div>
    </div>

    <script>
        // Auto-refresh every 10 seconds (polling fallback until SSE is implemented)
        setTimeout(() => {{
            window.location.reload();
        }}, 10000);
    </script>
</body>
</html>"""

    def _serve_status_json(self, include_loaded: bool = False) -> None:
        """Serve JSON API with node status and agent routes."""
        try:
            nodes = discover_fleet(self.server.fleet_config, include_loaded=include_loaded)
            routes = get_agent_routes(self.server.fleet_config)

            payload = {
                "fleet": self.server.fleet_config.project.name,
                "nodes": discovery_to_json(nodes),
                "routes": routes_to_json(routes),
            }

            self.send_response(200, "OK")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")  # Allow CORS for dev flexibility
            self.end_headers()
            self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))
        except Exception as exc:
            error_payload = {"error": str(exc)}
            self.send_response(500, "Internal Server Error")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(error_payload).encode("utf-8"))

    def _serve_static_file(self, filename: str) -> None:
        """Serve static files (CSS, JS, images) from the static directory."""
        file_path = self.server.static_dir / filename

        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "File Not Found")
            return

        # Determine content type based on file extension
        ext = file_path.suffix.lower()
        content_types = {
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".html": "text/html; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
        }

        content_type = content_types.get(ext, "application/octet-stream")

        try:
            with open(file_path, "rb") as f:
                file_content = f.read()

            self.send_response(200, "OK")
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "public, max-age=3600")  # Cache for 1 hour
            self.end_headers()
            self.wfile.write(file_content)
        except Exception as exc:
            self.send_error(500, f"Error reading file: {exc}")

    def _serve_sse(self) -> None:
        """Serve Server-Sent Events stream (Phase 2+)."""
        # Phase 2+: Implement SSE streaming for real-time updates
        # For now, return a placeholder message
        self.send_response(501, "Not Implemented")
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        self.wfile.write(b"event: error\ndata: {\"message\": \"SSE not yet implemented in this MVP\"}\n\n")

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default HTTP server logging to reduce noise."""
        # Uncomment below to enable verbose logging during development:
        # super().log_message(format, *args)
        pass


def create_dashboard_server(
    fleet_config: FleetConfig,
    host: str = "127.0.0.1",
    port: int = 8080,
) -> DashboardServer:
    """Factory function to create a configured DashboardServer instance.

    Args:
        fleet_config: Loaded FleetConfig from fleet.yaml.
        host: Host to bind to (default: 127.0.0.1).
        port: Port to bind to (default: 8080).

    Returns:
        Configured DashboardServer instance ready to serve_forever().
    """
    return DashboardServer(
        fleet_config=fleet_config,
        host=host,
        port=port,
    )
