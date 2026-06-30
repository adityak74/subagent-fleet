"""EVALS §1 — Fleet YAML Parsing & Validation."""

from __future__ import annotations
from pathlib import Path

import pytest
import yaml
from subagent_fleet.config import ConfigError, load_config


# ── Baselines ────────────────────────────────────────────────────────

MINIMAL = (
    "project: {name: demo}\n"
    "nodes: {local: {endpoint: http://localhost:11434}}\n"
    "models: {coder: {node: local, ollama_model: qwen, litellm_alias: test}}\n"
    "agents: {planner: {model: coder, description: Test agent}}"
)

VALID_3NODE = """project: {name: cluster, gateway: {host: 0.0.0.0, port: 4000}}
nodes:
  laptop:    {endpoint: http://localhost:11434, tags: [local]}
  mac64:     {endpoint: http://192.168.1.50:11434, tags: [heavy]}
  mac16:     {endpoint: http://192.168.1.51:11434, tags: [small]}
models:
  sonnet:    {node: mac64, ollama_model: qwen:latest, litellm_alias: llama}
  haiku:     {node: mac16, ollama_model: gemma:latest, litellm_alias: mistral}
agents:
  planner:   {model: sonnet, description: Plans tasks}
"""


# ── Positive cases ───────────────────────────────────────────────────

def test_minimal_loads(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(MINIMAL)
    cfg = load_config(p)
    assert cfg.project.name == "demo"
    assert "local" in cfg.nodes


def test_valid_3node_loads(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(VALID_3NODE)
    cfg = load_config(p)
    assert cfg.project.name == "cluster"
    assert len(cfg.nodes) == 3
    assert len(cfg.models) == 2
    assert len(cfg.agents) == 1


def test_cloud_node_without_endpoint(tmp_path: Path) -> None:
    """Cloud nodes may omit endpoint -- it is optional."""
    p = tmp_path / "fleet.yaml"
    p.write_text(
        "project: {name: x}\n"
        "nodes: {cloud: {cloud_provider: aws}}\n"
        "models: {coder: {node: cloud, ollama_model: claude, litellm_alias: t}}\n"
        "agents: {planner: {model: coder, description: a}}"
    )
    cfg = load_config(p)
    assert "cloud" in cfg.nodes


def test_min_prompt_handled(tmp_path: Path) -> None:
    """Empty string prompt still loads (AgentConfig accepts str | None)."""
    p = tmp_path / "fleet.yaml"
    p.write_text(
        "project: {name: x}\n"
        "nodes: {local: {endpoint: http://localhost:11434}}\n"
        "models: {coder: {node: local, ollama_model: qwen, litellm_alias: t}}\n"
        "agents: {planner: {model: coder, description: a, prompt: ''}}"
    )
    cfg = load_config(p)
    assert cfg.agents["planner"].prompt == ""


# ── Rejection cases ──────────────────────────────────────────────────

def test_duplicate_key_rejected(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    # Duplicate top-level key 'nodes'
    p.write_text(
        "project: {name: x}\n"
        "nodes: {a: {endpoint: http://localhost:11434}}\n"
        "nodes: {b: {endpoint: http://x:11434}}\n"
        "models: {coder: {node: a, ollama_model: qwen, litellm_alias: t}}\n"
        "agents: {a: {model: coder, description: b}}"
    )
    with pytest.raises(ConfigError, match="duplicate key"):
        load_config(p)


def test_missing_required_field_rejected(tmp_path: Path) -> None:
    """Missing 'name' on project should raise."""
    p = tmp_path / "fleet.yaml"
    # project has no name field at all
    p.write_text(
        "project: {}\n"
        "nodes: {local: {endpoint: http://localhost:11434}}\n"
        "models: {coder: {node: local, ollama_model: qwen, litellm_alias: t}}\n"
        "agents: {planner: {model: coder, description: a}}"
    )
    with pytest.raises(ConfigError):
        load_config(p)


def test_invalid_port_rejected(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(
        "project: {name: x, gateway: {host: 0.0.0.0, port: 66000}}\n"
        "nodes: {local: {endpoint: http://localhost:11434}}\n"
        "models: {coder: {node: local, ollama_model: qwen, litellm_alias: t}}\n"
        "agents: {planner: {model: coder, description: a}}"
    )
    with pytest.raises(ConfigError):
        load_config(p)


def test_bad_agent_name_rejected(tmp_path: Path) -> None:
    """Agent names must match ^[a-z0-9_-]+$."""
    p = tmp_path / "fleet.yaml"
    p.write_text(
        "project: {name: x}\n"
        "nodes: {local: {endpoint: http://localhost:11434}}\n"
        "models: {coder: {node: local, ollama_model: qwen, litellm_alias: t}}\n"
        "agents: {Planner: {model: coder, description: a}}"  # capital P
    )
    with pytest.raises(ConfigError):
        load_config(p)


def test_context_zero_rejected(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(
        "project: {name: x}\n"
        "nodes: {local: {endpoint: http://localhost:11434}}\n"
        "models: {coder: {node: local, ollama_model: qwen, litellm_alias: t, context: 0}}\n"
        "agents: {planner: {model: coder, description: a}}"
    )
    with pytest.raises(ConfigError):
        load_config(p)


def test_extra_field_rejected(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(
        "project: {name: x}\n"
        "nodes: {local: {endpoint: http://localhost:11434, unknown: 1}}\n"
        "models: {coder: {node: local, ollama_model: qwen, litellm_alias: t}}\n"
        "agents: {planner: {model: coder, description: a}}"
    )
    with pytest.raises(ConfigError):
        load_config(p)


def test_endpoint_not_valid_url_rejected(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(
        "project: {name: x}\n"
        "nodes: {local: {endpoint: not-a-valid-url}}\n"
        "models: {coder: {node: local, ollama_model: qwen, litellm_alias: t}}\n"
        "agents: {planner: {model: coder, description: a}}"
    )
    with pytest.raises(ConfigError):
        load_config(p)


# ── Reference checks (valid YAML but model_validator rejects) ─────────

def test_unknown_model_node_rejected(tmp_path: Path) -> None:
    """Model references node that doesn't exist."""
    p = tmp_path / "fleet.yaml"
    p.write_text(
        "project: {name: x}\n"
        "nodes: {local: {endpoint: http://localhost:11434}}\n"
        "models: {coder: {node: missing, ollama_model: qwen, litellm_alias: t}}\n"
        "agents: {planner: {model: coder, description: a}}"
    )
    with pytest.raises(ConfigError):
        load_config(p)


def test_unknown_agent_model_rejected(tmp_path: Path) -> None:
    """Agent references model that doesn't exist."""
    p = tmp_path / "fleet.yaml"
    p.write_text(
        "project: {name: x}\n"
        "nodes: {local: {endpoint: http://localhost:11434}}\n"
        "models: {coder: {node: local, ollama_model: qwen, litellm_alias: t}}\n"
        "agents: {planner: {model: missing_model, description: a}}"
    )
    with pytest.raises(ConfigError):
        load_config(p)
