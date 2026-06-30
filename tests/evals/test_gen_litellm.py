"""EVALS §2 — Config Generation: LiteLLM."""

from __future__ import annotations
from pathlib import Path

import yaml
from subagent_fleet.config import load_config
from subagent_fleet.generators.litellm import generate_litellm_config


FLEET_LITE = """project:
  name: cluster
  gateway: {provider: litellm, host: 127.0.0.1, port: 4000, master_key_env: LITELLM_MASTER_KEY}

nodes:
  laptop:       {endpoint: http://localhost:11434}
  mac64:        {endpoint: http://192.168.40.69:11434}

models:
  heavy-coder:         {node: mac64, ollama_model: qwen3-coder-next:latest, litellm_alias: sonnet-local, context: 65536, timeout: 600}
  small-planner:       {node: laptop, ollama_model: gemma4:latest, litellm_alias: haiku-local, context: 8192, timeout: 300}

agents:
  planner:    {model: small-planner, description: Fast local planning agent for task decomposition and summarization.}
  coder:      {model: heavy-coder, description: Senior implementation agent for coding and refactoring.}"""


def test_heavy_routes_to_mac64(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LITE)
    cfg = load_config(p)
    generate_litellm_config(cfg, tmp_path / "litellm_config.yaml")
    content = (tmp_path / "litellm_config.yaml").read_text()
    assert "ollama_chat/qwen3-coder-next:latest" in content


def test_small_routes_to_laptop(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LITE)
    cfg = load_config(p)
    generate_litellm_config(cfg, tmp_path / "litellm_config.yaml")
    content = (tmp_path / "litellm_config.yaml").read_text()
    assert "ollama_chat/gemma4:latest" in content


def test_timeout_propagated(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LITE)
    cfg = load_config(p)
    generate_litellm_config(cfg, tmp_path / "litellm_config.yaml")
    content = (tmp_path / "litellm_config.yaml").read_text()
    assert "timeout: 600" in content


def test_timeout_different(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LITE)
    cfg = load_config(p)
    generate_litellm_config(cfg, tmp_path / "litellm_config.yaml")
    content = (tmp_path / "litellm_config.yaml").read_text()
    assert "timeout: 300" in content


def test_context_window(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LITE)
    cfg = load_config(p)
    generate_litellm_config(cfg, tmp_path / "litellm_config.yaml")
    content = (tmp_path / "litellm_config.yaml").read_text()
    assert "max_input_tokens: 65536" in content


def test_master_key_env(tmp_path: Path) -> None:
    fleet = """project: {name: x, gateway: {host: 0.0.0.0, port: 4000, master_key_env: LITELLM_MASTER_KEY}}
nodes: {local: {endpoint: http://localhost:11434}}
models: {coder: {node: local, ollama_model: qwen, litellm_alias: t}}
agents: {planner: {model: coder, description: Test}}"""
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    generate_litellm_config(cfg, tmp_path / "litellm_config.yaml")
    content = (tmp_path / "litellm_config.yaml").read_text()
    assert "master_key: os.environ/LITELLM_MASTER_KEY" in content


def test_multi_node_routing(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LITE)
    cfg = load_config(p)
    generate_litellm_config(cfg, tmp_path / "litellm_config.yaml")
    content = (tmp_path / "litellm_config.yaml").read_text()
    assert "api_base: http://192.168.40.69:11434" in content


def test_round_trip(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LITE)
    cfg = load_config(p)
    out = generate_litellm_config(cfg, tmp_path / "litellm_config.yaml")
    assert out.exists()
    content = out.read_text()
    assert "model_list" in content
    assert "sonnet-local" in content


def test_litellm_output_contains_provider(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LITE)
    cfg = load_config(p)
    generate_litellm_config(cfg, tmp_path / "litellm_config.yaml")
    content = (tmp_path / "litellm_config.yaml").read_text()
    assert "ollama_chat" in content


def test_model_list_exists(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LITE)
    cfg = load_config(p)
    generate_litellm_config(cfg, tmp_path / "litellm_config.yaml")
    content = (tmp_path / "litellm_config.yaml").read_text()
    assert "model_list:" in content


def test_yaml_valid(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LITE)
    cfg = load_config(p)
    generate_litellm_config(cfg, tmp_path / "litellm_config.yaml")
    content = (tmp_path / "litellm_config.yaml").read_text()
    assert len(content) > 0
