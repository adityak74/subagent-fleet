"""HTTP/SSE server for the Fleet Dashboard.

Phase 2 architecture::

    ┌─────────────┐     SSE events      ┌──────────────┐
    │  Log tailer │ ─ ─ ─ ─ ─ ─ ─ ─ ─▶│              │
    │  (LiteLLM)  │                     │   Server     │
    │             │                     │   broadcast  │
    │ Warmup cmd  │ ─ ─ ─ ─ ─ ─ ─ ─ ─▶│   loop       │
    └─────────────┘                     └──────┬───────┘
                                               │
                                            clients
                                          (EventSource)

The server uses ThreadingHTTPServer so each client connection runs in its
own thread. A single background broadcast thread pushes events to all
connected SSE clients on a fixed interval. Discovery results are cached
with a TTL so repeated requests don't hammer Ollama.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from jinja2 import Environment, FileSystemLoader

from subagent_fleet.config import FleetConfig
from subagent_fleet.discovery import discovery_to_json, discover_fleet
from subagent_fleet.status import get_agent_routes, routes_to_json


logger = logging.getLogger(__name__)


# ── Discovery cache ───────────────────────────────────────────────

@dataclass(slots=True)
class _CachedDiscovery:
    """Thread-safe TTL cache entry for discovery results."""

    payload: dict[str, Any]
    fetched_at: float
    ttl_seconds: float = 30.0

    def is_fresh(self) -> bool:
        return (time.monotonic() - self.fetched_at) < self.ttl_seconds


class DiscoveryCache:
    """Simple in-memory TTL cache for discovery results."""

    def __init__(self, ttl: float = 30.0) -> None:
        self._ttl = ttl
        self._lock = threading.Lock()
        self._entry: _CachedDiscovery | None = None

    def get(self) -> dict[str, Any] | None:
        with self._lock:
            if self._entry is not None and self._entry.is_fresh():
                return self._entry.payload
            return None

    def put(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._entry = _CachedDiscovery(payload=payload, fetched_at=time.monotonic(), ttl_seconds=self._ttl)

    def invalidate(self) -> None:
        with self._lock:
            self._entry = None


# ── SSE broadcast ────────────────────────────────────────────────

class SSERenderer:
    """Minimal SSE wire-format renderer.

    Writes the standard ``data: …\\n\\n`` format with a proper Content-Type
    header and no-cache headers so browsers don't buffer events.
    """

    def __init__(self, handler: BaseHTTPRequestHandler) -> None:
        self._handler = handler

    def start(self) -> None:
        h = self._handler
        h.send_response(200, "OK")
        h.send_header("Content-Type", "text/event-stream; charset=utf-8")
        h.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        h.send_header("Connection", "keep-alive")
        h.send_header("X-Accel-Buffering", "no")  # nginx hint
        h.end_headers()

    def send_event(self, event: str, data: dict[str, Any]) -> None:
        payload = json.dumps(data).encode("utf-8")
        line = f"event: {event}\ndata: {payload.decode('utf-8')}\n\n".encode("utf-8")
        try:
            self._handler.wfile.write(line)
            self._handler.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            raise


@dataclass(slots=True)
class _ClientSlot:
    """Represents one connected SSE client."""

    renderer: SSERenderer
    last_heartbeat: float = field(default_factory=time.monotonic)


# ── Log tailer (LiteLLM trace stream source) ────────────────────

@dataclass(slots=True)
class _LogTailer:
    """Background thread that tails a LiteLLM log file and emits events.

    Designed to be started once when the server starts (if a log path is
    configured). Reads new lines from the end of the file on a short interval
    and pushes parsed trace-log SSE events into the broadcast queue.
    """

    log_path: str
    event_callback: Any  # Callable[[str, dict], None] — emit_trace_log(name, data)
    poll_interval: float = 0.3
    _stop_event: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread | None = field(default=None, init=False)

    def start(self) -> None:
        if self.log_path and os.path.exists(self.log_path):
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True, name="log-tailer")
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        f = open(self._log_path, "r", errors="replace")
        try:
            f.seek(0, 2)  # seek to end
            while not self._stop_event.is_set():
                line = f.readline()
                if not line:
                    time.sleep(self.poll_interval)
                    continue
                parsed = _parse_litellm_line(line.rstrip("\n"))
                if parsed is not None:
                    event_name, data = parsed
                    try:
                        self.event_callback(event_name, data)
                    except Exception:
                        pass  # don't crash the tailer on broadcast error
        finally:
            f.close()


def _parse_litellm_line(line: str) -> tuple[str, dict[str, Any]] | None:
    """Parse a raw LiteLLM log line into an SSE event name + data payload.

    Returns None if the line doesn't match any known pattern.
    """
    stripped = line.strip()
    if not stripped:
        return None

    now = time.time()

    # Errors (most specific)
    if "Exception" in stripped or "Error" in stripped:
        return ("trace-log", {"level": "error", "message": stripped, "timestamp": _iso_now()})

    # Routing events — POST to chat completions endpoint
    if "POST /v1/chat/completions" in stripped or "POST /chat/completions" in stripped:
        return ("trace-log", {"level": "routing", "message": f"Request routed: {stripped}", "timestamp": _iso_now()})

    # Success codes
    if "200 OK" in stripped:
        return ("trace-log", {"level": "success", "message": stripped, "timestamp": _iso_now()})

    # Model selection hints
    if "API Base" in stripped or "Model:" in stripped:
        return ("trace-log", {"level": "routing", "message": stripped, "timestamp": _iso_now()})

    return None


def _iso_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ── Request handler ──────────────────────────────────────────────

class DashboardRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Fleet Dashboard.

    Routes:
        - GET /dashboard or GET / : HTML dashboard page (Jinja2 template)
        - GET /api/status?include_loaded=true : JSON API with node status + routes
        - GET /static/* : Static assets (CSS, JS)
        - GET /api/events : SSE endpoint for real-time updates
        - POST /api/warmup-progress : Push warmup progress event

    Accesses server state via self.server (set by ThreadingHTTPServer).
    """

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET requests."""
        path = self.path.split("?")[0]

        if path == "/dashboard" or path == "/":
            self._serve_dashboard_page()
        elif path.startswith("/api/status"):
            params = parse_qs(self.path.split("?", 1)[1]) if "?" in self.path else {}
            include_loaded = params.get("include_loaded", ["false"])[0].lower() == "true"
            self._serve_status_json(include_loaded=include_loaded)
        elif path.startswith("/static/"):
            filename = path[len("/static/"):]
            self._serve_static_file(filename)
        elif path == "/api/events":
            self._serve_sse()
        else:
            self.send_error(404, "Not Found")

    def do_HEAD(self) -> None:  # noqa: N802
        """Handle HEAD requests (health checks)."""
        path = self.path.split("?")[0]
        if path == "/dashboard" or path == "/" or path.startswith("/api/"):
            self.send_response(200, "OK")
            self.end_headers()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:  # noqa: N802
        """Handle POST requests — used for warmup progress push events."""
        path = self.path.split("?")[0]
        if path == "/api/warmup-progress":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length else ""

            # Parse SSE-style data: "data: {...}\n\n" or raw JSON.
            payload: dict[str, Any] = {}
            if body.startswith("data:"):
                try:
                    payload = json.loads(body[len("data:"):].strip())
                except (ValueError, TypeError):
                    pass
            else:
                try:
                    payload = json.loads(body)
                except (ValueError, TypeError):
                    pass

            # Validate required fields.
            model_name = payload.get("model_name", "")
            node_name = payload.get("node_name", "")
            status = payload.get("status", "pending")

            if not model_name or not node_name:
                self.send_error(400, "Missing model_name or node_name")
                return

            # Broadcast to all SSE clients via server.
            event_data = {"model_name": model_name, "node_name": node_name, "status": status}
            self.server._emit_to_clients("warmup-progress", event_data)

            self.send_response(204, "No Content")
            self.end_headers()
        else:
            self.send_error(404, "Not Found")

    # ── Response helpers (access server state via self.server) ──

    def _serve_dashboard_page(self) -> None:
        """Render the dashboard from a Jinja2 template."""
        srv = self.server  # type: DashboardServer
        try:
            tmpl = srv._jinja_env.get_template("dashboard.html")
            html_content = tmpl.render(fleet_name=srv.fleet_config.project.name)
        except Exception as exc:
            self.send_error(500, f"Template error: {exc}")
            return

        self.send_response(200, "OK")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def _serve_status_json(self, include_loaded: bool = False) -> None:
        """Serve JSON API with node status and agent routes. Uses cache."""
        srv = self.server  # type: DashboardServer
        try:
            # Try cache first for discovery data.
            cached = srv.cache.get()
            if cached is not None and include_loaded is False:
                payload = dict(cached)  # shallow copy
            else:
                nodes = discover_fleet(srv.fleet_config, include_loaded=include_loaded)
                routes = get_agent_routes(srv.fleet_config)
                payload = {
                    "fleet": srv.fleet_config.project.name,
                    "nodes": discovery_to_json(nodes),
                    "routes": routes_to_json(routes),
                }
                # Cache the result for future requests.
                if include_loaded is False:
                    srv.cache.put(payload)

            self.send_response(200, "OK")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
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
        srv = self.server  # type: DashboardServer
        file_path = (srv.static_dir / filename).resolve()

        # Path traversal guard — reject any path that escapes static_dir.
        if not str(file_path).startswith(str(srv.static_dir.resolve())):
            self.send_error(403, "Forbidden")
            return

        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "File Not Found")
            return

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
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(file_content)
        except Exception as exc:
            self.send_error(500, f"Error reading file: {exc}")

    def _serve_sse(self) -> None:
        """Handle SSE client connection."""
        srv = self.server  # type: DashboardServer
        slot = srv._register_client(self)
        try:
            # Block until the client disconnects (server shuts down or
            # browser closes the tab). The broadcast loop pushes events.
            while not srv._broadcast_stop.is_set():
                time.sleep(1.0)
        except (BrokenPipeError, ConnectionResetError):
            pass  # client disconnected
        finally:
            srv._unregister_client(slot)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default HTTP server logging to reduce noise."""
        pass


# ── Server ───────────────────────────────────────────────────────

class DashboardServer(ThreadingHTTPServer):
    """HTTP/SSE server for the Fleet Dashboard.

    Serves:
        - /dashboard or / : HTML dashboard page (Jinja2 template)
        - /api/status?include_loaded=true : JSON API with node status + routes
        - /static/* : Static assets (CSS, JS) from ui/static/
        - /api/events : SSE endpoint for real-time updates

    Inherits ThreadingHTTPServer so each client connection gets its own thread.
    A single background broadcast thread pushes events to all connected SSE
    clients on a fixed interval. Discovery results are cached with a TTL.
    """

    def __init__(
        self,
        fleet_config: FleetConfig,
        host: str = "127.0.0.1",
        port: int = 8080,
        static_dir: Path | None = None,
        templates_dir: Path | None = None,
        log_path: str | None = None,
    ) -> None:
        super().__init__((host, port), DashboardRequestHandler)
        self.fleet_config = fleet_config

        # Resolve template / static directories (defaults to package dirs).
        pkg_dir = Path(__file__).parent
        self.static_dir = static_dir or (pkg_dir / "static")
        tmpl_dir = templates_dir or (pkg_dir / "templates")
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(tmpl_dir)),
            autoescape=False,  # We escape in JS, not server-side HTML
        )

        # Discovery cache — shared across all requests.
        self.cache = DiscoveryCache(ttl=30.0)

        # SSE client registry (thread-safe).
        self._clients_lock = threading.Lock()
        self._clients: list[_ClientSlot] = []

        # Background broadcast thread.
        self._broadcast_stop = threading.Event()
        self._broadcast_thread: threading.Thread | None = None

        # Log tailer for trace stream events (optional).
        self.log_tailer = _LogTailer(
            log_path=log_path or "",
            event_callback=self._emit_to_clients,
        )

    def serve_forever(self) -> None:
        """Start serving. Starts broadcast loop and optional log tailer."""
        # Start the background broadcast thread.
        self._broadcast_stop.clear()
        self._broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True, name="sse-broadcast")
        self._broadcast_thread.start()

        # Optionally start the LiteLLM log tailer.
        if self.log_tailer:
            self.log_tailer.start()

        super().serve_forever()

    def shutdown(self) -> None:
        """Signal all background threads and shut down."""
        self._broadcast_stop.set()
        if self.log_tailer:
            self.log_tailer.stop()
        # Close all SSE client connections.
        with self._clients_lock:
            for slot in self._clients:
                try:
                    slot.renderer.start()  # ensure headers sent so client knows we're done
                except Exception:
                    pass
            self._clients.clear()
        super().shutdown()

    # ── Broadcast helpers ────────────────────────────────────

    def _emit_to_clients(self, event_name: str, data: dict[str, Any]) -> None:
        """Push an SSE event to all connected clients (called from background)."""
        payload = json.dumps(data)
        line = f"event: {event_name}\ndata: {payload}\n\n".encode("utf-8")

        with self._clients_lock:
            dead: list[int] = []
            for i, slot in enumerate(self._clients):
                try:
                    slot.renderer._handler.wfile.write(line)
                    slot.renderer._handler.wfile.flush()
                    slot.last_heartbeat = time.monotonic()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    dead.append(i)
            # Prune dead clients.
            for i in reversed(dead):
                self._clients.pop(i)

    def _broadcast_loop(self) -> None:
        """Background loop that pushes node-status + agent-route events every 10s."""
        while not self._broadcast_stop.is_set():
            try:
                # Always fetch fresh discovery data for SSE (not cached).
                nodes = discover_fleet(self.fleet_config, include_loaded=False)
                routes = get_agent_routes(self.fleet_config)

                node_payload = {"nodes": discovery_to_json(nodes)}
                route_payload = {"routes": routes_to_json(routes)}

                self._emit_to_clients("node-status", node_payload)
                self._emit_to_clients("agent-route", route_payload)
            except Exception as exc:
                logger.debug("broadcast error: %s", exc, exc_info=True)

            # Sleep in small increments so we can stop quickly.
            for _ in range(50):  # 10 s / 0.2 s per check
                if self._broadcast_stop.is_set():
                    break
                time.sleep(0.2)

    def _register_client(self, handler: BaseHTTPRequestHandler) -> _ClientSlot:
        """Register a new SSE client and return its slot."""
        renderer = SSERenderer(handler)
        renderer.start()  # send headers immediately
        slot = _ClientSlot(renderer=renderer)
        with self._clients_lock:
            self._clients.append(slot)
        return slot

    def _unregister_client(self, slot: _ClientSlot | None) -> None:
        """Remove a client from the registry (called on disconnect)."""
        if slot is None:
            return
        with self._clients_lock:
            try:
                self._clients.remove(slot)
            except ValueError:
                pass

    # ── Factory ──────────────────────────────────────────────

def create_dashboard_server(
    fleet_config: FleetConfig,
    host: str = "127.0.0.1",
    port: int = 8080,
    log_path: str | None = None,
) -> DashboardServer:
    """Factory function to create a configured DashboardServer instance.

    Args:
        fleet_config: Loaded FleetConfig from fleet.yaml.
        host: Host to bind to (default: 127.0.0.1).
        port: Port to bind to (default: 8080).
        log_path: Optional path to a LiteLLM debug log file for trace streaming.

    Returns:
        Configured DashboardServer instance ready to serve_forever().
    """
    return DashboardServer(
        fleet_config=fleet_config,
        host=host,
        port=port,
        log_path=log_path,
    )
