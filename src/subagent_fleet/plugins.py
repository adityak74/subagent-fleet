from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from subagent_fleet.skills import BUNDLED_SKILLS, load_skill_template

PLUGIN_NAME = "subagent-fleet"
PLUGIN_VERSION = "0.1.7"
PLUGIN_DESCRIPTION = "Run Claude Code-style subagents across your local Ollama and LiteLLM model fleet."
PLUGIN_REPOSITORY = "https://github.com/adityak74/subagent-fleet"
PLUGIN_HOMEPAGE = "https://github.com/adityak74/subagent-fleet#readme"


class PluginInstallError(ValueError):
    """Raised when assistant plugin marketplace files cannot be installed."""


@dataclass(frozen=True, slots=True)
class PluginInstallResult:
    target: str
    path: Path


def install_plugin_marketplaces(*, output_root: Path, targets: list[str], force: bool = False) -> list[PluginInstallResult]:
    resolved_targets = resolve_plugin_targets(targets)
    results: list[PluginInstallResult] = []
    plugin_root = output_root / "plugins" / PLUGIN_NAME

    for target in resolved_targets:
        if target == "codex":
            results.extend(_install_codex(output_root, plugin_root, force=force))
        elif target == "claude-code":
            results.extend(_install_claude(output_root, plugin_root, force=force))
        else:
            raise PluginInstallError(f"unknown target: {target}")

    _install_plugin_skills(plugin_root, force=force)
    return results


def resolve_plugin_targets(values: list[str] | None) -> list[str]:
    names = _split_values(values or ["all"])
    allowed = {"all", "codex", "claude-code"}
    unknown = sorted(set(names) - allowed)
    if unknown:
        raise PluginInstallError(f"unknown plugin target: {', '.join(unknown)}")
    if "all" in names:
        if len(names) > 1:
            raise PluginInstallError("Use either all or specific plugin targets, not both")
        return ["claude-code", "codex"]
    return names


def _install_codex(output_root: Path, plugin_root: Path, *, force: bool) -> list[PluginInstallResult]:
    marketplace_path = output_root / ".agents" / "plugins" / "marketplace.json"
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    _write_json(marketplace_path, codex_marketplace(), force=force)
    _write_json(manifest_path, codex_plugin_manifest(), force=force)
    return [
        PluginInstallResult(target="codex", path=marketplace_path),
        PluginInstallResult(target="codex", path=manifest_path),
    ]


def _install_claude(output_root: Path, plugin_root: Path, *, force: bool) -> list[PluginInstallResult]:
    marketplace_path = output_root / ".claude-plugin" / "marketplace.json"
    manifest_path = plugin_root / ".claude-plugin" / "plugin.json"
    _write_json(marketplace_path, claude_marketplace(), force=force)
    _write_json(manifest_path, claude_plugin_manifest(), force=force)
    return [
        PluginInstallResult(target="claude-code", path=marketplace_path),
        PluginInstallResult(target="claude-code", path=manifest_path),
    ]


def _install_plugin_skills(plugin_root: Path, *, force: bool) -> None:
    for skill in BUNDLED_SKILLS.values():
        skill_path = plugin_root / "skills" / skill.name / "SKILL.md"
        _write_text(skill_path, load_skill_template(skill), force=force)


def claude_marketplace() -> dict:
    return {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": PLUGIN_NAME,
        "description": "Marketplace for the subagent-fleet Claude Code plugin.",
        "owner": {
            "name": "Aditya Karnam",
            "url": "https://github.com/adityak74",
        },
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "description": PLUGIN_DESCRIPTION,
                "author": {
                    "name": "Aditya Karnam",
                    "url": "https://github.com/adityak74",
                },
                "category": "development",
                "source": "./plugins/subagent-fleet",
                "homepage": PLUGIN_HOMEPAGE,
            }
        ],
    }


def claude_plugin_manifest() -> dict:
    return {
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "description": PLUGIN_DESCRIPTION,
        "author": {
            "name": "Aditya Karnam",
            "url": "https://github.com/adityak74",
        },
        "repository": PLUGIN_REPOSITORY,
        "license": "MIT",
        "keywords": [
            "claude-code",
            "subagents",
            "ollama",
            "litellm",
            "local-ai",
            "python",
        ],
        "homepage": PLUGIN_HOMEPAGE,
    }


def codex_marketplace() -> dict:
    return {
        "name": PLUGIN_NAME,
        "interface": {
            "displayName": "subagent-fleet",
        },
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "source": {
                    "source": "local",
                    "path": "./plugins/subagent-fleet",
                },
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": "Productivity",
            }
        ],
    }


def codex_plugin_manifest() -> dict:
    return {
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "description": PLUGIN_DESCRIPTION,
        "author": {
            "name": "Aditya Karnam",
            "url": "https://github.com/adityak74",
        },
        "homepage": PLUGIN_HOMEPAGE,
        "repository": PLUGIN_REPOSITORY,
        "license": "MIT",
        "keywords": [
            "codex",
            "claude-code",
            "subagents",
            "ollama",
            "litellm",
            "local-ai",
            "python",
        ],
        "skills": "./skills/",
        "interface": {
            "displayName": "subagent-fleet",
            "shortDescription": "Configure local subagent fleets with Ollama and LiteLLM.",
            "longDescription": PLUGIN_DESCRIPTION,
            "developerName": "Aditya Karnam",
            "category": "Productivity",
            "capabilities": [
                "Interactive",
                "Write",
            ],
            "websiteURL": PLUGIN_REPOSITORY,
            "defaultPrompt": [
                "Install subagent-fleet and set up a local fleet.",
                "Generate LiteLLM and Claude agent config.",
                "Troubleshoot my local Ollama subagent routes.",
            ],
            "brandColor": "#2563EB",
        },
    }


def _write_json(path: Path, data: dict, *, force: bool) -> None:
    _write_text(path, json.dumps(data, indent=2) + "\n", force=force)


def _write_text(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; use --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _split_values(values: list[str]) -> list[str]:
    names: list[str] = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                names.append(item)
    if not names:
        raise PluginInstallError("at least one plugin target is required")
    return names
