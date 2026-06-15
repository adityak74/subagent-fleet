from __future__ import annotations

import json
from pathlib import Path

from subagent_fleet.plugins import claude_marketplace, codex_marketplace, codex_plugin_manifest


def test_checked_in_claude_marketplace_points_to_plugin() -> None:
    marketplace = json.loads(Path(".claude-plugin/marketplace.json").read_text())

    assert marketplace["$schema"] == "https://anthropic.com/claude-code/marketplace.schema.json"
    assert marketplace["name"] == "subagent-fleet"
    assert marketplace["plugins"][0]["source"] == "./plugins/subagent-fleet"


def test_checked_in_codex_marketplace_has_required_policy() -> None:
    marketplace = json.loads(Path(".agents/plugins/marketplace.json").read_text())
    plugin = marketplace["plugins"][0]

    assert marketplace["name"] == "subagent-fleet"
    assert plugin["source"] == {"source": "local", "path": "./plugins/subagent-fleet"}
    assert plugin["policy"] == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}
    assert plugin["category"] == "Productivity"


def test_checked_in_plugin_bundle_has_bootstrap_skill() -> None:
    skill = Path("plugins/subagent-fleet/skills/subagent-fleet-bootstrap/SKILL.md").read_text()

    assert "python -m pip install" in skill
    assert "subagent-fleet skills install" in skill


def test_generated_marketplaces_match_checked_in_files() -> None:
    assert json.loads(Path(".claude-plugin/marketplace.json").read_text()) == claude_marketplace()
    assert json.loads(Path(".agents/plugins/marketplace.json").read_text()) == codex_marketplace()
    assert json.loads(Path("plugins/subagent-fleet/.codex-plugin/plugin.json").read_text()) == codex_plugin_manifest()
