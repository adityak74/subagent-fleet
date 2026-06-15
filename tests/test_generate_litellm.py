from __future__ import annotations

from subagent_fleet.config import load_config
from subagent_fleet.generators.litellm import generate_litellm_config


def test_litellm_output_contains_ollama_provider_and_api_base(tmp_path) -> None:
    config = load_config("tests/fixtures/fleet.yaml")
    output = tmp_path / "litellm_config.yaml"

    generate_litellm_config(config, output)

    content = output.read_text()
    assert "ollama_chat/qwen2.5-coder:32b" in content
    assert "api_base: http://192.168.1.50:11434" in content
    assert "master_key: os.environ/LITELLM_MASTER_KEY" in content
