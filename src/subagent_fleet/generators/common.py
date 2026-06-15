from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from subagent_fleet.config import FleetConfig


def template_env() -> Environment:
    return Environment(
        loader=PackageLoader("subagent_fleet", "templates"),
        autoescape=select_autoescape(default=False),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def write_generated(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; use --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def default_aliases(config: FleetConfig) -> tuple[str | None, str | None]:
    sonnet = None
    haiku = None
    for model_name, model in config.models.items():
        lowered = f"{model_name} {model.litellm_alias} {model.ollama_model}".lower()
        if sonnet is None and ("heavy" in lowered or "sonnet" in lowered or "32b" in lowered):
            sonnet = model.litellm_alias
        if haiku is None and ("small" in lowered or "haiku" in lowered or "7b" in lowered):
            haiku = model.litellm_alias
    if sonnet is None and config.models:
        sonnet = next(iter(config.models.values())).litellm_alias
    if haiku is None and config.models:
        haiku = next(iter(config.models.values())).litellm_alias
    return sonnet, haiku
