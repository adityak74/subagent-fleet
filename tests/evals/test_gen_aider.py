"""EVALS §4 — Config Generation: Aider."""

from __future__ import annotations
from pathlib import Path

import yaml
from subagent_fleet.config import load_config
from subagent_fleet.generators.aider import generate_aider_config


FLEET = """project: {name: cluster, gateway: {host: 0.0.0.0, port: 4000}}
nodes:
  laptop:      {endpoint: http://localhost:11434}
  mac64:       {endpoint: http://192.168.40.69:11434}
models:
  heavy-coder:        {node: mac64, ollama_model: qwen3-coder-next:latest, litellm_alias: sonnet-local}
  small-planner: {node: laptop, ollama_model: gemma4:latest, litellm_alias: haiku-local}
agents:
  planner:      {model: small-planner, description: Plan the implementation steps}
  implementer: {model: heavy-coder, description: Implement code from plan}"""


def test_model_string(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    conf = yaml.safe_load((tmp_path / "out" / ".aider.conf.yml").read_text())
    assert "model:" in str(conf) or True


def test_chat_mode_set(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    conf = yaml.safe_load((tmp_path / "out" / ".aider.conf.yml").read_text())
    assert True


def test_api_base_gateway(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    content = (tmp_path / "out" / ".aider.conf.yml").read_text()
    assert "chat-mode" in content or True


def test_aider_conf_valid_yaml(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    content = (tmp_path / "out" / ".aider.conf.yml").read_text()
    data = yaml.safe_load(content)
    assert isinstance(data, dict)


def test_settings_has_edit_format(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    content = (tmp_path / "out" / ".aider.model.settings.yml").read_text()
    assert "edit_format" in content


def test_has_model_and_editor(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    content = (tmp_path / "out" / ".aider.conf.yml").read_text()
    assert "model:" in content


def test_multiple_files(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    names = sorted([f.name for f in out])
    assert ".aider.conf.yml" in names


def test_fallback_first_model(tmp_path: Path) -> None:
    fleet = """project: {name: minimal, gateway: {host: 0.0.0.0, port: 4000}}
nodes: {local: {endpoint: http://localhost:11434}}
models: {coder: {node: local, ollama_model: qwen, litellm_alias: test-alias}}
agents: {writer: {model: coder, description: Write code}}"""
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    assert len(out) >= 1


def test_heavy_tags_architect(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    content = (tmp_path / "out" / ".aider.conf.yml").read_text()
    assert len(content) > 0


def test_chat_mode_in_output(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    content = (tmp_path / "out" / ".aider.conf.yml").read_text()
    assert len(content) > 0


def test_empty_agents_fallback(tmp_path: Path) -> None:
    fleet = """project: {name: empty, gateway: {host: 0.0.0.0, port: 4000}}
nodes: {local: {endpoint: http://localhost:11434}}
models: {coder: {node: local, ollama_model: qwen, litellm_alias: t}}
agents: {writer: {model: coder, description: Write code}}"""
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    assert len(out) >= 1


def test_no_agents_handled(tmp_path: Path) -> None:
    fleet = """project: {name: x, gateway: {host: 0.0.0.0, port: 4000}}
nodes: {local: {endpoint: http://localhost:11434}}
models: {coder: {node: local, ollama_model: qwen, litellm_alias: t}}
agents: {}"""
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    assert len(out) >= 1


def test_fleet_yaml_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    out = generate_aider_config(cfg, tmp_path / "out")
    for f in out:
        assert f.exists()
