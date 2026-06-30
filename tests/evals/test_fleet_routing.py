"""EVALS -- Agent Routing."""

from __future__ import annotations
from pathlib import Path

import pytest
from subagent_fleet.config import ConfigError, load_config
from subagent_fleet.status import get_agent_routes, routes_to_json
from subagent_fleet.warmup import select_models


FLEET = """project: {name: cluster, gateway: {host: 0.0.0.0, port: 4000}}
nodes: {mac16: {endpoint: http://192.168.40.59:11434, tags: [small]}, mac64: {endpoint: http://192.168.40.69:11434, tags: [heavy, coder]}, laptop: {endpoint: http://localhost:11434, tags: [local]}}
models: {heavy-coder: {node: mac64, ollama_model: qwen3-coder-next:latest, litellm_alias: sonnet-local}, small-planner: {node: mac16, ollama_model: gemma4:latest, litellm_alias: haiku-local}, local-agent: {node: laptop, ollama_model: qwen3.6:35b-mlx, litellm_alias: sonnet-alt}}
agents: {planner: {model: small-planner, description: Plan tasks and discover files.}, implementer: {model: heavy-coder, description: Implement code changes and fixes.}, reviewer: {model: heavy-coder, description: Review diffs for correctness.}}"""


def test_planner_routes_small(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    routes = get_agent_routes(cfg)
    planner = next(r for r in routes if r.agent == "planner")
    assert planner.node == "mac16"
    assert planner.ollama_model == "gemma4:latest"


def test_implementer_routes_heavy(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    routes = get_agent_routes(cfg)
    impl = next(r for r in routes if r.agent == "implementer")
    assert impl.node == "mac64"
    assert impl.ollama_model == "qwen3-coder-next:latest"


def test_reviewer_same_as_implementer(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    routes = get_agent_routes(cfg)
    rev = next(r for r in routes if r.agent == "reviewer")
    impl = next(r for r in routes if r.agent == "implementer")
    assert rev.node == impl.node
    assert rev.ollama_model == impl.ollama_model


def test_all_agents_have_routes(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    routes = get_agent_routes(cfg)
    agents = {r.agent for r in routes}
    assert agents == {"planner", "implementer", "reviewer"}


def test_agent_count_matches(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    assert len(cfg.agents) == 3
    assert len(get_agent_routes(cfg)) == 3


def test_json_produces_dicts(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    routes = get_agent_routes(cfg)
    j = routes_to_json(routes)
    assert isinstance(j, list)
    for item in j:
        assert "agent" in item


def test_select_models_all(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    models = select_models(cfg)
    assert set(models) == {"heavy-coder", "small-planner", "local-agent"}


def test_select_models_by_name(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    models = select_models(cfg, model_name="heavy-coder")
    assert models == ["heavy-coder"]


def test_select_models_by_agent(tmp_path: Path) -> None:
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET)
    cfg = load_config(p)
    models = select_models(cfg, agent_name="planner")
    assert models == ["small-planner"]


def test_empty_agents_no_routes(tmp_path: Path) -> None:
    empty_yaml = "project: {name: empty, gateway: {host: 0.0.0.0, port: 4000}}\nnodes: {local: {endpoint: http://localhost:11434}}\nmodels: {coder: {node: local, ollama_model: qwen, litellm_alias: test}}\nagents: {}"
    p = tmp_path / "fleet.yaml"
    p.write_text(empty_yaml)
    cfg = load_config(p)
    assert get_agent_routes(cfg) == []


def test_missing_model_ref_raises(tmp_path: Path) -> None:
    bad = "project: {name: x, gateway: {host: 0.0.0.0, port: 4000}}\nnodes: {local: {endpoint: http://localhost:11434}}\nmodels: {coder: {node: local, ollama_model: qwen, litellm_alias: t}}\nagents: {planner: {model: missing-model, description: Plans things.}}"
    p = tmp_path / "fleet.yaml"
    p.write_text(bad)
    with pytest.raises(ConfigError):
        load_config(p)
