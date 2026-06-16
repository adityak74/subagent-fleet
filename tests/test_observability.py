import pytest
from subagent_fleet.config import ObservabilityConfig, ProjectConfig, FleetConfig, GatewayConfig
from subagent_fleet.generators import generate_litellm_config, generate_env_file
from pathlib import Path

def test_observability_defaults():
    obs = ObservabilityConfig()
    assert obs.langfuse is False
    assert obs.langsmith is False
    assert obs.opentelemetry is False

def test_observability_config_parsing():
    config = FleetConfig.model_validate({
        "project": {
            "name": "test",
            "observability": {
                "langfuse": True,
                "langsmith": False
            }
        },
        "nodes": {},
        "models": {},
        "agents": {}
    })
    assert config.project.observability.langfuse is True
    assert config.project.observability.langsmith is False
    assert config.project.observability.opentelemetry is False

def test_generate_litellm_with_observability(tmp_path):
    config = FleetConfig.model_validate({
        "project": {
            "name": "test",
            "observability": {
                "langfuse": True,
                "opentelemetry": True
            }
        },
        "nodes": {},
        "models": {},
        "agents": {}
    })
    output_path = tmp_path / "litellm_config.yaml"
    generate_litellm_config(config, output_path)
    
    content = output_path.read_text()
    assert "success_callbacks:" in content
    assert "- langfuse" in content
    assert "- otel" in content
    assert "failure_callbacks:" in content

def test_generate_env_with_observability(tmp_path):
    config = FleetConfig.model_validate({
        "project": {
            "name": "test",
            "observability": {
                "langsmith": True
            }
        },
        "nodes": {},
        "models": {},
        "agents": {}
    })
    output_path = tmp_path / ".env.subagent-fleet"
    generate_env_file(config, output_path)
    
    content = output_path.read_text()
    assert "LANGCHAIN_API_KEY" in content
    assert "LANGCHAIN_PROJECT=\"test\"" in content
    assert "LANGFUSE_PUBLIC_KEY" not in content
