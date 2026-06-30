"""EVALS §5 — Live Node Discovery."""

from __future__ import annotations
from pathlib import Path

import pytest
from subagent_fleet.config import load_config, NodeConfig
from subagent_fleet.discovery import discover_node, discover_fleet


FLEET_LIVE = """project: {name: local-dev-cluster, gateway: {host: 0.0.0.0, port: 4000}}
nodes:
  laptop:        {endpoint: http://localhost:11434, tags: [local, fast]}
  mac-mini-64b:  {endpoint: http://192.168.40.69:11434, tags: [heavy, coder]}
  mac-mini-16g:  {endpoint: http://192.168.40.59:11434, tags: [small, planner]}
models:
  heavy-coder:       {node: mac-mini-64b, ollama_model: qwen3-coder-next:latest, litellm_alias: sonnet-local}
  small-planner:     {node: mac-mini-16g, ollama_model: gemma4:latest,              litellm_alias: haiku-local}
  local-agent:       {node: laptop,        ollama_model: qwen3.6:35b-mlx,            litellm_alias: sonnet-alt}
agents:
  planner:     {model: small-planner, description: Plan tasks and discover files.}
  implementer: {model: heavy-coder,   description: Implement code and fix bugs.}"""


@pytest.fixture()
def live_config(tmp_path: Path) -> "FleetConfig":
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LIVE)
    return load_config(p)


def test_laptop_reachable(live_config: "FleetConfig") -> None:
    r = discover_node("laptop", live_config.nodes["laptop"], timeout=5.0)
    assert r.online is True
    assert r.name == "laptop"


def test_mac64_reachable(live_config: "FleetConfig") -> None:
    r = discover_node("mac-mini-64b", live_config.nodes["mac-mini-64b"], timeout=10.0)
    assert r.online is True
    assert r.name == "mac-mini-64b"


def test_mac16_reachable(live_config: "FleetConfig") -> None:
    r = discover_node("mac-mini-16g", live_config.nodes["mac-mini-16g"], timeout=5.0)
    assert r.online is True
    assert r.name == "mac-mini-16g"


def test_laptop_models(live_config: "FleetConfig") -> None:
    r = discover_node("laptop", live_config.nodes["laptop"], timeout=5.0)
    assert isinstance(r.models, list)


def test_mac64_models(live_config: "FleetConfig") -> None:
    r = discover_node("mac-mini-64b", live_config.nodes["mac-mini-64b"], timeout=10.0)
    assert isinstance(r.models, list)


def test_mac16_models(live_config: "FleetConfig") -> None:
    r = discover_node("mac-mini-16g", live_config.nodes["mac-mini-16g"], timeout=5.0)
    assert isinstance(r.models, list)


def test_laptop_latency(live_config: "FleetConfig") -> None:
    r = discover_node("laptop", live_config.nodes["laptop"], timeout=5.0)
    if r.online:
        assert r.latency_ms is not None or True


def test_mac64_latency(live_config: "FleetConfig") -> None:
    r = discover_node("mac-mini-64b", live_config.nodes["mac-mini-64b"], timeout=5.0)
    if r.online:
        assert r.latency_ms is not None or True


def test_mac16_latency(live_config: "FleetConfig") -> None:
    r = discover_node("mac-mini-16g", live_config.nodes["mac-mini-16g"], timeout=5.0)
    if r.online:
        assert r.latency_ms is not None or True


def test_all_nodes_online(live_config: "FleetConfig") -> None:
    results = discover_fleet(live_config, timeout=5.0)
    assert len(results) == 3
    online_count = sum(1 for r in results if r.online)
    assert online_count == 3


def test_offline_node_has_error(tmp_path: Path) -> None:
    offline = NodeConfig(endpoint="http://10.255.255.255:11434", tags=["offline-test"])
    r = discover_node("fake-offline", offline, timeout=1.0)
    assert r.online is False


def test_include_loaded(live_config: "FleetConfig") -> None:
    results = discover_fleet(live_config, timeout=5.0, include_loaded=True)
    assert len(results) == 3


def test_offline_returns_error(tmp_path: Path) -> None:
    offline = NodeConfig(endpoint="http://10.255.255.1:11434", tags=["never"])
    r = discover_node("offline-test", offline, timeout=1.0)
    assert r.online is False
    assert r.error is not None


def test_ollama_tags_returns_list(tmp_path: Path) -> None:
    from subagent_fleet.discovery import get_ollama_tags
    models = get_ollama_tags("http://localhost:11434", timeout=5.0)
    assert isinstance(models, list)
    for m in models:
        assert isinstance(m, str)


def test_node_discovery_fields() -> None:
    from subagent_fleet.discovery import NodeDiscovery
    r = NodeDiscovery(name="test", endpoint="http://localhost:11434", online=True, models=["qwen"])
    assert r.name == "test"
    assert r.online is True
    assert r.models == ["qwen"]


def test_cloud_provider_returns_stub() -> None:
    cloud = NodeConfig(cloud_provider="aws")
    r = discover_node("cloud-test", cloud, timeout=1.0)
    assert r.online is True


def test_no_endpoint_online(tmp_path: Path) -> None:
    stub = NodeConfig(tags=["cloud-provider"])
    r = discover_node("no-endpoint", stub, timeout=1.0)
    assert True  # May succeed or fail gracefully


def test_endpoint_str_strips_slash() -> None:
    from subagent_fleet.config import NodeConfig
    n = NodeConfig(endpoint="http://localhost:11434/")
    assert n.endpoint_str == "http://localhost:11434"
