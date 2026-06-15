from __future__ import annotations

from subagent_fleet.config import load_config
from subagent_fleet.generators.claude_agents import generate_claude_agents
from subagent_fleet.generators.env_file import generate_env_file


def test_claude_agent_markdown_has_frontmatter(tmp_path) -> None:
    config = load_config("tests/fixtures/fleet.yaml")

    generate_claude_agents(config, tmp_path)

    content = (tmp_path / "planner.md").read_text()
    assert "---" in content
    assert "name: planner" in content
    assert "model: claude-haiku-local" in content
    assert "tools: Read, Grep, Glob" in content


def test_env_file_contains_anthropic_base_url(tmp_path) -> None:
    config = load_config("tests/fixtures/fleet.yaml")
    output = tmp_path / ".env.subagent-fleet"

    generate_env_file(config, output)

    assert 'export ANTHROPIC_BASE_URL="http://localhost:4000"' in output.read_text()
