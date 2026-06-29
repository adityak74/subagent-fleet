"""Unit tests for Fleet Dashboard UI events module."""

from __future__ import annotations

import json

import pytest

from subagent_fleet.ui.events import (
    AgentRouteEvent,
    LogLineParser,
    NodeStatusEvent,
    TraceLogEvent,
    WarmupProgressEvent,
    serialize_event,
)


class TestNodeStatusEvent:
    """Tests for NodeStatusEvent serialization."""

    def test_to_sse_format(self) -> None:
        """Verify SSE wire format has correct event name and data field."""
        nodes = [
            {"name": "local", "online": True, "models": ["qwen2.5-coder:7b"]},
            {"name": "remote", "online": False, "error": "Connection refused"},
        ]
        event = NodeStatusEvent(nodes=nodes)

        sse_output = event.to_sse()

        assert sse_output.startswith("event: node-status\n")
        # Check that data field exists (contains "data:" after the event line)
        assert "\ndata: {" in sse_output
        assert sse_output.endswith("\n\n"), "SSE events must end with double newline"

    def test_to_sse_serializes_valid_json(self) -> None:
        """Verify data payload is valid JSON."""
        nodes = [{"name": "test-node", "online": True, "models": []}]
        event = NodeStatusEvent(nodes=nodes)

        # Extract data field from SSE output
        sse_output = event.to_sse()
        data_line = sse_output.split("\n")[1]  # Second line is 'data: ...'
        json_str = data_line[len("data: ") :]

        parsed = json.loads(json_str)
        assert parsed["nodes"][0]["name"] == "test-node"
        assert parsed["nodes"][0]["online"] is True


class TestAgentRouteEvent:
    """Tests for AgentRouteEvent serialization."""

    def test_to_sse_format(self) -> None:
        """Verify SSE wire format has correct event name."""
        routes = [
            {"agent": "planner", "node": "local-ollama", "ollama_model": "qwen2.5-coder:7b", "litellm_alias": "haiku-local"},
        ]
        event = AgentRouteEvent(routes=routes)

        sse_output = event.to_sse()

        assert sse_output.startswith("event: agent-route\n")


class TestTraceLogEvent:
    """Tests for TraceLogEvent serialization and timestamp generation."""

    def test_default_timestamp_is_set(self) -> None:
        """Verify timestamp is automatically set if not provided."""
        event = TraceLogEvent(level="success", message="200 OK")

        assert event.timestamp != ""
        # Should be a valid ISO format string
        from datetime import datetime, timezone

        parsed = datetime.fromisoformat(event.timestamp)
        assert parsed.tzinfo == timezone.utc

    def test_custom_timestamp_is_preserved(self) -> None:
        """Verify explicit timestamp is not overwritten."""
        custom_ts = "2026-01-01T00:00:00Z"
        event = TraceLogEvent(level="success", message="test", timestamp=custom_ts)

        assert event.timestamp == custom_ts


class TestWarmupProgressEvent:
    """Tests for WarmupProgressEvent serialization."""

    def test_to_sse_format(self) -> None:
        """Verify SSE wire format has correct event name."""
        event = WarmupProgressEvent(model_name="heavy-coder", node_name="m4-mini-64gb", status="ok")

        sse_output = event.to_sse()

        assert sse_output.startswith("event: warmup-progress\n")


class TestLogLineParser:
    """Tests for LogLineParser on known log patterns."""

    def setup_method(self) -> None:
        self.parser = LogLineParser()

    def test_parses_post_chat_completions_as_routing(self) -> None:
        """Verify POST /v1/chat/completions lines are parsed as routing events."""
        line = 'POST /v1/chat/completions HTTP/1.1" 200 OK'
        result = self.parser.parse(line)

        assert result is not None
        assert result.level == "routing"
        assert "Request routed:" in result.message

    def test_parses_200_ok_as_success(self) -> None:
        """Verify '200 OK' lines are parsed as success events."""
        line = 'HTTP/1.1 200 OK'
        result = self.parser.parse(line)

        assert result is not None
        assert result.level == "success"

    def test_parses_exception_as_error(self) -> None:
        """Verify Exception/Error lines are parsed as error events."""
        line = 'Exception in thread "main": java.lang.NullPointerException'
        result = self.parser.parse(line)

        assert result is not None
        assert result.level == "error"

    def test_parses_api_base_as_routing(self) -> None:
        """Verify API Base lines are parsed as routing events."""
        line = 'API Base: http://192.168.1.50:11434'
        result = self.parser.parse(line)

        assert result is not None
        assert result.level == "routing"

    def test_parses_model_selection_as_routing(self) -> None:
        """Verify Model: lines are parsed as routing events."""
        line = 'Model: qwen2.5-coder:32b'
        result = self.parser.parse(line)

        assert result is not None
        assert result.level == "routing"

    def test_returns_none_for_empty_line(self) -> None:
        """Verify empty lines return None."""
        result = self.parser.parse("")
        assert result is None

    def test_returns_none_for_unrecognized_pattern(self) -> None:
        """Verify unrecognized patterns return None (not a crash)."""
        line = "This is an unrecognized log line"
        result = self.parser.parse(line)
        assert result is None


class TestSerializeEvent:
    """Tests for the serialize_event helper function."""

    def test_serializes_node_status_event(self) -> None:
        """Verify serialize_event works with NodeStatusEvent."""
        event = NodeStatusEvent(nodes=[])
        sse_output = serialize_event(event)

        assert sse_output.startswith("event: node-status\n")

    def test_raises_type_error_for_unsupported_event(self) -> None:
        """Verify TypeError is raised for events without to_sse method."""

        class UnsupportedEvent:
            pass

        with pytest.raises(TypeError, match="does not have a to_sse"):
            serialize_event(UnsupportedEvent())
