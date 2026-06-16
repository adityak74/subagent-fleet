import pytest
from typer.testing import CliRunner
from subagent_fleet.cli import app
from pathlib import Path

runner = CliRunner()

def test_trace_command_file_not_found():
    result = runner.invoke(app, ["trace", "--log-file", "nonexistent_log.log"])
    assert result.exit_code == 1
    assert "not found" in result.stdout

def test_trace_command_success(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text("POST /chat/completions\nModel: ollama_chat/qwen2.5\n")
    
    # We can't easily test the infinite loop, but we can verify it starts up without error.
    # We'll patch the while loop to raise KeyboardInterrupt to simulate user exit.
    from unittest.mock import patch
    with patch("time.sleep", side_effect=KeyboardInterrupt):
        result = runner.invoke(app, ["trace", "--log-file", str(log_file)])
        assert result.exit_code == 0
        assert "Tracking subagent fleet activity" in result.stdout
        assert "Stopped tracing" in result.stdout
