from __future__ import annotations

from pathlib import Path

from subagent_fleet.config import FleetConfig
from subagent_fleet.generators.common import template_env, write_generated


def generate_claude_agents(config: FleetConfig, output_dir: Path, *, source: str = "fleet.yaml", force: bool = False) -> list[Path]:
    template = template_env().get_template("claude_agent.md.j2")
    written: list[Path] = []
    for agent_name, agent in config.agents.items():
        model = config.models[agent.model]
        content = template.render(agent_name=agent_name, agent=agent, model=model, source=source)
        path = output_dir / f"{agent_name}.md"
        write_generated(path, content, force=force)
        written.append(path)
    return written
