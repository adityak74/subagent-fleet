from __future__ import annotations

from pathlib import Path

import pytest

from subagent_fleet.config import ConfigError, load_config


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "fleet.yaml"
    path.write_text(text)
    return path


def test_valid_example_config_loads() -> None:
    config = load_config(Path("tests/fixtures/fleet.yaml"))

    assert config.project.name == "local-dev"
    assert config.models["small-coder"].context == 8192
    assert config.models["small-coder"].timeout == 300
    assert config.models["small-coder"].max_parallel == 1


def test_rejects_unknown_node_reference(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
project: {name: demo}
nodes:
  local: {endpoint: http://localhost:11434}
models:
  coder:
    node: missing
    ollama_model: qwen
    litellm_alias: claude-local
agents:
  planner:
    model: coder
    description: Use for planning.
""",
    )

    with pytest.raises(ConfigError, match="unknown node"):
        load_config(path)


def test_rejects_unknown_model_reference(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
project: {name: demo}
nodes:
  local: {endpoint: http://localhost:11434}
models:
  coder:
    node: local
    ollama_model: qwen
    litellm_alias: claude-local
agents:
  planner:
    model: missing
    description: Use for planning.
""",
    )

    with pytest.raises(ConfigError, match="unknown model"):
        load_config(path)


def test_rejects_invalid_url(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
project: {name: demo}
nodes:
  local: {endpoint: localhost:11434}
models:
  coder:
    node: local
    ollama_model: qwen
    litellm_alias: claude-local
agents:
  planner:
    model: coder
    description: Use for planning.
""",
    )

    with pytest.raises(ConfigError, match="URL"):
        load_config(path)


def test_rejects_unsafe_agent_name(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
project: {name: demo}
nodes:
  local: {endpoint: http://localhost:11434}
models:
  coder:
    node: local
    ollama_model: qwen
    litellm_alias: claude-local
agents:
  "Plan Agent":
    model: coder
    description: Use for planning.
""",
    )

    with pytest.raises(ConfigError, match="filesystem-safe"):
        load_config(path)


def test_rejects_duplicate_mapping_keys(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
project: {name: demo}
nodes:
  local: {endpoint: http://localhost:11434}
  local: {endpoint: http://127.0.0.1:11434}
models:
  coder:
    node: local
    ollama_model: qwen
    litellm_alias: claude-local
agents:
  planner:
    model: coder
    description: Use for planning.
""",
    )

    with pytest.raises(ConfigError, match="duplicate key"):
        load_config(path)
