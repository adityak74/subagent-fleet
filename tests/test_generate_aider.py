import pytest
from pathlib import Path
from subagent_fleet.config import FleetConfig
from subagent_fleet.generators.aider import generate_aider_config

def test_generate_aider_config(tmp_path):
    config = FleetConfig.model_validate({
        "project": {"name": "test"},
        "nodes": {
            "heavy-node": {"endpoint": "http://1.1.1.1:11434", "tags": ["heavy"]},
            "fast-node": {"endpoint": "http://2.2.2.2:11434", "tags": ["fast"]}
        },
        "models": {
            "big-model": {"node": "heavy-node", "ollama_model": "big:32b", "litellm_alias": "claude-sonnet-local"},
            "small-model": {"node": "fast-node", "ollama_model": "small:7b", "litellm_alias": "claude-haiku-local"}
        },
        "agents": {
            "implementer": {"model": "big-model", "description": "impl"},
            "planner": {"model": "small-model", "description": "plan"}
        }
    })
    
    generated = generate_aider_config(config, tmp_path)
    
    assert len(generated) == 2
    
    conf_content = (tmp_path / ".aider.conf.yml").read_text()
    assert "chat-mode: architect" in conf_content
    assert "model: openai/claude-sonnet-local" in conf_content
    assert "editor-model: openai/claude-haiku-local" in conf_content
    
    settings_content = (tmp_path / ".aider.model.settings.yml").read_text()
    assert "edit_format: whole" in settings_content
