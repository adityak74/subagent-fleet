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
