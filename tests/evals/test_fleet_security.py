"""EVALS section 10 -- Security and Edge Cases."""

from __future__ import annotations
from pathlib import Path

import yaml
from subagent_fleet.config import load_config


def test_endpoint_injection_rejected(tmp_path: Path) -> None:
    """Malicious endpoint with invalid URL is rejected by Pydantic."""
    fleet = yaml.dump({
        'project': {'name': 'insecure', 'gateway': {
            'host': '0.0.0.0', 'port': 4000}},
        'nodes': {'evil': {'endpoint': 'not-a-url'}},
        'models': {'coder': {
            'node': 'evil', 'ollama_model': 'qwen',
            'litellm_alias': 'test'}},
        'agents': {'planner': {
            'model': 'coder', 'description': 'Plan tasks'}},
    })
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    try:
        load_config(p)
    except Exception:
        return
    assert False, "Should have raised for invalid endpoint"


def test_valid_url_accepted(tmp_path: Path) -> None:
    """Valid HTTP endpoint with path is accepted by Pydantic."""
    fleet = yaml.dump({
        'project': {'name': 'demo', 'gateway': {
            'host': '0.0.0.0', 'port': 4000}},
        'nodes': {'evil': {
            'endpoint': 'http://evil.com/test'}},
        'models': {'coder': {
            'node': 'evil', 'ollama_model': 'qwen',
            'litellm_alias': 'test'}},
        'agents': {'planner': {
            'model': 'coder', 'description': 'Plan'}},
    })
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    assert "evil" in cfg.nodes


def test_master_key_env_nested(tmp_path: Path) -> None:
    """Master key env var nested inside project gateway."""
    fleet = yaml.dump({
        'project': {'name': 'demo', 'gateway': {
            'host': '0.0.0.0', 'port': 4000,
            'master_key_env': 'LITELLM_MASTER_KEY'}},
        'nodes': {'local': {
            'endpoint': 'http://localhost:11434'}},
        'models': {'coder': {
            'node': 'local', 'ollama_model': 'qwen',
            'litellm_alias': 'test'}},
        'agents': {'planner': {
            'model': 'coder', 'description': 'Plan'}},
    })
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    assert cfg.project.gateway.master_key_env == "LITELLM_MASTER_KEY"


def test_empty_agents_handled(tmp_path: Path) -> None:
    """Empty agents block loads without crash."""
    fleet = yaml.dump({
        'project': {'name': 'empty', 'gateway': {
            'host': '0.0.0.0', 'port': 4000}},
        'nodes': {'local': {
            'endpoint': 'http://localhost:11434'}},
        'models': {'coder': {
            'node': 'local', 'ollama_model': 'qwen',
            'litellm_alias': 'test'}},
        'agents': {},
    })
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    assert len(cfg.agents) == 0


def test_duplicate_aliases_warns(tmp_path: Path) -> None:
    """Two models with same litellm_alias triggers a warning."""
    fleet = yaml.dump({
        'project': {'name': 'dup', 'gateway': {
            'host': '0.0.0.0', 'port': 4000}},
        'nodes': {
            'n1': {'endpoint': 'http://localhost:11434'},
            'n2': {'endpoint': 'http://10.0.0.2:11434'},
        },
        'models': {
            'm1': {'node': 'n1', 'ollama_model': 'qwen',
                   'litellm_alias': 'same-alias'},
            'm2': {'node': 'n2', 'ollama_model': 'llama',
                   'litellm_alias': 'same-alias'},
        },
        'agents': {
            'planner': {'model': 'm1', 'description': 'Test'},
        },
    })
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    assert len(cfg.models) == 2
    aliases = [m.litellm_alias for m in cfg.models.values()]
    assert aliases.count("same-alias") == 2


def test_duplicate_aliases_produces_warning(tmp_path: Path) -> None:
    """Duplicate aliases produce at least one warning entry."""
    fleet = yaml.dump({
        'project': {'name': 'dup', 'gateway': {
            'host': '0.0.0.0', 'port': 4000}},
        'nodes': {
            'n1': {'endpoint': 'http://localhost:11434'},
            'n2': {'endpoint': 'http://10.0.0.2:11434'},
        },
        'models': {
            'm1': {'node': 'n1', 'ollama_model': 'qwen',
                   'litellm_alias': 'same-alias'},
            'm2': {'node': 'n2', 'ollama_model': 'llama',
                   'litellm_alias': 'same-alias'},
        },
        'agents': {
            'planner': {'model': 'm1', 'description': 'Test'},
        },
    })
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    warnings = list(cfg.alias_warnings())
    assert len(warnings) >= 1


def test_long_prompt_handled(tmp_path: Path) -> None:
    """Very long agent prompt (50k chars) loads without crash."""
    long_desc = "x" * 50000
    fleet = yaml.dump({
        'project': {'name': 'x', 'gateway': {
            'host': '0.0.0.0', 'port': 4000}},
        'nodes': {'local': {
            'endpoint': 'http://localhost:11434'}},
        'models': {'coder': {
            'node': 'local', 'ollama_model': 'qwen',
            'litellm_alias': 't'}},
        'agents': {'planner': {
            'model': 'coder', 'description': long_desc}},
    })
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    assert len(cfg.agents["planner"].description) == 50000
