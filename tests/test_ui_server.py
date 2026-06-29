"""Integration tests for Fleet Dashboard UI server."""

from __future__ import annotations

import socket
import threading
import time

import httpx
import pytest

from subagent_fleet.config import FleetConfig, load_config
from subagent_fleet.ui.server import DashboardServer, create_dashboard_server


@pytest.fixture(scope="module")
def test_config_path(tmp_path_factory):
    """Create a temporary fleet.yaml for testing."""
    config_content = """
project:
  name: test-fleet

nodes:
  local-node:
    endpoint: http://localhost:11434
    tags: [controller, local]

models:
  small-coder:
    node: local-node
    ollama_model: qwen2.5-coder:7b
    litellm_alias: haiku-local
    context: 8192
    timeout: 300
    max_parallel: 1

agents:
  planner:
    model: small-coder
    description: Use for planning tasks.
"""
    config_path = tmp_path_factory.mktemp("config").joinpath("fleet.yaml")
    config_path.write_text(config_content)
    return config_path


@pytest.fixture(scope="module")
def running_server(test_config_path):
    """Start a test DashboardServer and yield its port."""
    fleet = load_config(test_config_path)

    # Use port 0 to let OS assign a random available port
    server = create_dashboard_server(
        fleet_config=fleet,
        host="127.0.0.1",
        port=0,
    )

    # Get the actual bound port (OS-assigned)
    _, bound_port = server.server_address

    # Start server in background thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    # Wait for server to be ready
    time.sleep(0.5)

    yield {"server": server, "port": bound_port}

    # Shutdown
    server.shutdown()


class TestDashboardServerStartup:
    """Tests for DashboardServer startup and shutdown."""

    def test_server_starts_and_accepts_connections(self, running_server):
        """Verify the server starts and accepts TCP connections."""
        port = running_server["port"]

        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass  # Connection succeeded


class TestStaticFileServing:
    """Tests for static file serving (Phase 2+)."""

    def test_static_file_not_found(self, running_server):
        """Verify 404 is returned for missing static files."""
        port = running_server["port"]

        with httpx.Client() as client:
            response = client.get(f"http://127.0.0.1:{port}/static/nonexistent.css")
            assert response.status_code == 404


class TestStatusEndpoint:
    """Tests for /api/status JSON endpoint."""

    def test_status_endpoint_returns_json(self, running_server):
        """Verify /api/status returns valid JSON with expected structure."""
        port = running_server["port"]

        with httpx.Client() as client:
            response = client.get(f"http://127.0.0.1:{port}/api/status")
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]

            data = response.json()
            assert "fleet" in data
            assert "nodes" in data
            assert "routes" in data
            assert data["fleet"] == "test-fleet"  # From test fixture

    def test_status_endpoint_with_include_loaded(self, running_server):
        """Verify /api/status?include_loaded=true returns loaded_models field."""
        port = running_server["port"]

        with httpx.Client() as client:
            response = client.get(f"http://127.0.0.1:{port}/api/status?include_loaded=true")
            assert response.status_code == 200

            data = response.json()
            # NodeDiscovery has loaded_models field when include_loaded=True
            for node in data["nodes"]:
                assert "loaded_models" in node


class TestDashboardPage:
    """Tests for the HTML dashboard page."""

    def test_dashboard_page_returns_html(self, running_server):
        """Verify /dashboard returns HTML content."""
        port = running_server["port"]

        with httpx.Client() as client:
            response = client.get(f"http://127.0.0.1:{port}/dashboard")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            # Check that the page contains expected content from test fixture
            assert "test-fleet" in response.text

    def test_root_redirects_to_dashboard(self, running_server):
        """Verify / redirects to /dashboard (or serves dashboard inline)."""
        port = running_server["port"]

        with httpx.Client(follow_redirects=False) as client:
            response = client.get(f"http://127.0.0.1:{port}/")
            # Either redirect (3xx) or serve directly (200) are acceptable
            assert response.status_code in [200, 301, 302]
