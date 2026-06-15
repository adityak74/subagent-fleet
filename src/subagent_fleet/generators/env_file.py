from __future__ import annotations

from pathlib import Path

from subagent_fleet.config import FleetConfig
from subagent_fleet.generators.common import default_aliases, template_env, write_generated


def generate_env_file(config: FleetConfig, output_path: Path, *, source: str = "fleet.yaml", force: bool = False) -> Path:
    template = template_env().get_template("env.subagent-fleet.j2")
    default_sonnet_model, default_haiku_model = default_aliases(config)
    content = template.render(
        project=config.project,
        default_sonnet_model=default_sonnet_model,
        default_haiku_model=default_haiku_model,
        source=source,
    )
    write_generated(output_path, content, force=force)
    return output_path
