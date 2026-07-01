"""Shared fixtures for fleet eval tests.

All live-cluster tests use a real `fleet.yaml` from the project root.
Static-only tests use inline YAML to avoid network calls.
"""

from __future__ import annotations

import json
import time
import threading
import httpx
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

PROJECT_ROOT = Path(__file__).parent.parent.parent  # /Users/.../subagent-fleet
LIVE_FLEET_PATH = PROJECT_ROOT / "fleet.yaml"

# ── Helpers ────────────────────────────────────────────────────────────────


def _load_fleet(path: str | Path) -> dict:
    """Load fleet.yaml as a plain dict (avoids Pydantic validation in fixtures)."""
    with open(path) as fh:
        return yaml.safe_load(fh)


# ── Fixtures: live cluster ────────────────────────────────────────────────


@pytest.fixture(scope="session")
def live_fleet_path() -> Path:
    """Path to the real fleet.yaml in project root."""
    assert LIVE_FLEET_PATH.exists(), "fleet.yaml not found in project root"
    return LIVE_FLEET_PATH


@pytest.fixture(scope="session")
def live_fleet(live_fleet_path: Path) -> dict:
    """Live fleet config as a plain dict (project, nodes, models, agents)."""
    return _load_fleet(live_fleet_path)


@pytest.fixture(scope="session")
def live_nodes(live_fleet: dict) -> dict:
    return live_fleet.get("nodes", {})


@pytest.fixture(scope="session")
def live_models(live_fleet: dict) -> dict:
    return live_fleet.get("models", {})


@pytest.fixture(scope="session")
def live_agents(live_fleet: dict) -> dict:
    return live_fleet.get("agents", {})


@pytest.fixture(scope="session")
def project_name(live_fleet: dict) -> str:
    return live_fleet["project"]["name"]


# ── Fixtures: static (no network) ─────────────────────────────────────────


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    """Temp directory for generated-output tests."""
    return tmp_path


@pytest.fixture()
def fleet_yaml(live_fleet: dict) -> str:
    """Round-trip live fleet.yaml as a YAML string (for write_text fixtures)."""
    return yaml.dump(live_fleet, default_flow_style=False)


# ── Fixtures: CLI ─────────────────────────────────────────────────────────

@pytest.fixture()
def cli_runner() -> CliRunner:
    return CliRunner()


# ── Fixtures: HTTP helpers ────────────────────────────────────────────────


@pytest.fixture(scope="session")
def ollama_base_url(live_nodes: dict) -> str:
    """Return the first localhost node endpoint (laptop)."""
    for name, node in live_nodes.items():
        ep = node.get("endpoint", "")
        if "localhost" in ep or "127.0.0.1" in ep:
            return ep
    # Fallback to first endpoint
    first_endpoint = next(iter(live_nodes.values())).get("endpoint", "http://localhost:11434")
    return first_endpoint


@pytest.fixture(scope="session")
def http_client() -> httpx.Client:
    """Shared httpx client for Ollama HTTP calls in evals."""
    with httpx.Client(timeout=30.0) as client:
        yield client


@pytest.fixture()
def mock_ollama_tags(monkeypatch: pytest.MonkeyPatch) -> "callable":
    """Return a factory that sets up httpx.MockTransport for /api/tags.

    Usage:
        tags = mock_ollama_tags(["qwen:7b", "llama3:8b"])
        # now any discover_node call will see those models
    """
    from httpx import Response, MockTransport, Client as HttpxClient

    def _factory(models: list[str]) -> None:
        transport = MockTransport(
            lambda req: Response(200, json={"models": [{"name": m} for m in models]})
        )

        class MockClient(HttpxClient):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, transport=transport, **kwargs)

        monkeypatch.setattr("httpx.Client", MockClient)

    return _factory


@pytest.fixture()
def mock_ollama_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make all Ollama endpoints unreachable."""
    from httpx import NetworkError

    def _raise(*args, **kwargs):
        raise NetworkError("Connection refused")

    monkeypatch.setattr("httpx.Client.get", _raise)


# ── Convinience: skip markers ──────────────────────────────────────────────

import pytest


def pytest_addoption(parser):
    """Register --run-live flag for live cluster evals."""
    parser.addoption("--run-live", action="store_true", default=False, help="Enable live cluster eval tests")


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Skip live tests unless --run-live is passed."""
    if item.get_closest_marker("live") and not item.config.getoption("--run-live", default=False):
        pytest.skip("skipping live cluster eval — pass --run-live to enable")
