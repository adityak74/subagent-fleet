from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from subagent_fleet.cli import app

runner = CliRunner()


def test_init_creates_fleet_yaml(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--output", str(tmp_path / "fleet.yaml")])

    assert result.exit_code == 0
    assert (tmp_path / "fleet.yaml").exists()


def test_validate_passes_on_example() -> None:
    result = runner.invoke(app, ["validate", "--config", "tests/fixtures/fleet.yaml"])

    assert result.exit_code == 0
    assert "is valid" in result.output


def test_generate_creates_expected_files(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["generate", "--config", "tests/fixtures/fleet.yaml", "--out", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert (tmp_path / "litellm_config.yaml").exists()
    assert (tmp_path / ".claude" / "agents" / "planner.md").exists()
    assert (tmp_path / ".env.subagent-fleet").exists()


def test_status_json_includes_routes() -> None:
    result = runner.invoke(app, ["status", "--config", "tests/fixtures/fleet.yaml", "--json"])

    assert result.exit_code == 0
    assert '"agent": "planner"' in result.output
    assert '"litellm_alias": "claude-haiku-local"' in result.output


def test_skills_install_all_targets(tmp_path: Path) -> None:
    result = runner.invoke(app, ["skills", "install", "--out", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "skills" / "subagent-fleet-setup" / "SKILL.md").exists()
    assert (tmp_path / ".codex" / "skills" / "subagent-fleet-setup" / "SKILL.md").exists()
    assert (tmp_path / ".opencode" / "skills" / "subagent-fleet-operations" / "SKILL.md").exists()


def test_skills_install_specific_target_and_skill(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "skills",
            "install",
            "--out",
            str(tmp_path),
            "--target",
            "codex",
            "--skill",
            "subagent-fleet-setup",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / ".codex" / "skills" / "subagent-fleet-setup" / "SKILL.md").exists()
    assert not (tmp_path / ".claude" / "skills").exists()


def test_skills_install_does_not_overwrite_without_force(tmp_path: Path) -> None:
    first = runner.invoke(app, ["skills", "install", "--out", str(tmp_path), "--target", "codex"])
    second = runner.invoke(app, ["skills", "install", "--out", str(tmp_path), "--target", "codex"])

    assert first.exit_code == 0
    assert second.exit_code == 1
    assert "already exists" in second.output


def test_skills_list_shows_targets() -> None:
    result = runner.invoke(app, ["skills", "list"])

    assert result.exit_code == 0
    assert "subagent-fleet-setup" in result.output
    assert "claude-code" in result.output
    assert "opencode" in result.output


def test_plugins_install_all_targets(tmp_path: Path) -> None:
    result = runner.invoke(app, ["plugins", "install", "--out", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / ".claude-plugin" / "marketplace.json").exists()
    assert (tmp_path / ".agents" / "plugins" / "marketplace.json").exists()
    assert (tmp_path / "plugins" / "subagent-fleet" / ".claude-plugin" / "plugin.json").exists()
    assert (tmp_path / "plugins" / "subagent-fleet" / ".codex-plugin" / "plugin.json").exists()
    assert (tmp_path / "plugins" / "subagent-fleet" / "skills" / "subagent-fleet-bootstrap" / "SKILL.md").exists()


def test_plugins_install_specific_target(tmp_path: Path) -> None:
    result = runner.invoke(app, ["plugins", "install", "--out", str(tmp_path), "--target", "codex"])

    assert result.exit_code == 0
    assert (tmp_path / ".agents" / "plugins" / "marketplace.json").exists()
    assert not (tmp_path / ".claude-plugin").exists()


def test_plugins_install_does_not_overwrite_without_force(tmp_path: Path) -> None:
    first = runner.invoke(app, ["plugins", "install", "--out", str(tmp_path), "--target", "claude-code"])
    second = runner.invoke(app, ["plugins", "install", "--out", str(tmp_path), "--target", "claude-code"])

    assert first.exit_code == 0
    assert second.exit_code == 1
    assert "already exists" in second.output
