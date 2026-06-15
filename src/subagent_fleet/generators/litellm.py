from __future__ import annotations

from pathlib import Path

from subagent_fleet.config import FleetConfig
from subagent_fleet.generators.common import template_env, write_generated


def generate_litellm_config(config: FleetConfig, output_path: Path, *, source: str = "fleet.yaml", force: bool = False) -> Path:
    template = template_env().get_template("litellm_config.yaml.j2")
    content = template.render(project=config.project, nodes=config.nodes, models=config.models, source=source)
    write_generated(output_path, content, force=force)
    return output_path
