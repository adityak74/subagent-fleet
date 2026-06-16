from __future__ import annotations

from pathlib import Path

from subagent_fleet.config import FleetConfig
from subagent_fleet.generators.common import template_env, write_generated


def generate_aider_config(config: FleetConfig, output_dir: Path, *, source: str = "fleet.yaml", force: bool = False) -> list[Path]:
    template = template_env().get_template("aider_conf.yml.j2")
    
    architect_model = None
    editor_model = None
    
    # Heuristic: Find architect (heavy) and editor (fast/small) based on node tags or agents
    # Often, implementer/reviewer use heavy models
    for agent_name, agent in config.agents.items():
        if agent_name in ("implementer", "reviewer"):
            architect_model = config.models[agent.model].litellm_alias
        elif agent_name == "planner":
            editor_model = config.models[agent.model].litellm_alias

    # Fallback to tags
    if not architect_model:
        for model in config.models.values():
            node = config.nodes[model.node]
            if "heavy" in node.tags or "coder" in node.tags:
                architect_model = model.litellm_alias
                break
                
    if not editor_model:
        for model in config.models.values():
            node = config.nodes[model.node]
            if "fast" in node.tags or "local" in node.tags or "small" in node.tags:
                editor_model = model.litellm_alias
                break
                
    # Final fallback
    if not architect_model and config.models:
        architect_model = list(config.models.values())[0].litellm_alias
    if not editor_model and config.models:
        editor_model = architect_model

    content = template.render(
        architect_model=architect_model,
        editor_model=editor_model,
        source=source
    )
    path = output_dir / ".aider.conf.yml"
    write_generated(path, content, force=force)
    
    settings_template = template_env().get_template("aider_model_settings.yml.j2")
    settings_content = settings_template.render(source=source)
    settings_path = output_dir / ".aider.model.settings.yml"
    write_generated(settings_path, settings_content, force=force)
    
    return [path, settings_path]
