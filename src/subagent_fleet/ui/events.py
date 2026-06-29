"""Event types and utilities for SSE streaming in the Fleet Dashboard."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class NodeStatusEvent:
    """Event representing a full snapshot of node discovery results."""

    nodes: list[dict[str, Any]]

    def to_sse(self) -> str:
        """Serialize to SSE wire format (event name + data payload)."""
        return f"event: node-status\ndata: {json.dumps(asdict(self))}\n\n"


@dataclass(slots=True)
class AgentRouteEvent:
    """Event representing agent routing table updates."""

    routes: list[dict[str, str]]

    def to_sse(self) -> str:
        """Serialize to SSE wire format."""
        return f"event: agent-route\ndata: {json.dumps(asdict(self))}\n\n"


@dataclass(slots=True)
class TraceLogEvent:
    """Event representing a parsed LiteLLM log line."""

    level: str  # "success", "error", "routing", etc.
    message: str
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_sse(self) -> str:
        """Serialize to SSE wire format."""
        return f"event: trace-log\ndata: {json.dumps(asdict(self))}\n\n"


@dataclass(slots=True)
class WarmupProgressEvent:
    """Event representing warmup progress for a single model."""

    model_name: str
    node_name: str
    status: str  # "ok", "error: <reason>", etc.

    def to_sse(self) -> str:
        """Serialize to SSE wire format."""
        return f"event: warmup-progress\ndata: {json.dumps(asdict(self))}\n\n"


class LogLineParser:
    """Parse raw LiteLLM log lines into structured TraceLogEvent objects.

    Recognizes patterns from the existing `trace` CLI command:
        - "POST /v1/chat/completions" or "POST /chat/completions" → routing event
        - "200 OK" → success event
        - "Exception" or "Error" → error event
        - "API Base" or "Model:" → model selection event
    """

    def parse(self, line: str) -> TraceLogEvent | None:
        """Parse a single log line into a TraceLogEvent.

        Args:
            line: Raw log line from LiteLLM output.

        Returns:
            Parsed TraceLogEvent if the line matches a known pattern, None otherwise.
        """
        stripped = line.strip()
        if not stripped:
            return None

        # Check for error patterns first (most specific)
        if "Exception" in stripped or "Error" in stripped:
            return TraceLogEvent(level="error", message=stripped)

        # Check for routing patterns BEFORE success codes - POST to chat completions is always a routing event
        if "POST /v1/chat/completions" in stripped or "POST /chat/completions" in stripped:
            return TraceLogEvent(level="routing", message=f"Request routed: {stripped}")

        # Check for success/status codes (after routing to avoid false positives)
        if "200 OK" in stripped:
            return TraceLogEvent(level="success", message=stripped)

        # Check for model selection hints
        if "API Base" in stripped or "Model:" in stripped:
            return TraceLogEvent(level="routing", message=stripped)

        # Unknown pattern - return None (caller can decide how to handle)
        return None


def serialize_event(event: NodeStatusEvent | AgentRouteEvent | TraceLogEvent | WarmupProgressEvent) -> str:
    """Serialize any supported event type to SSE wire format.

    Args:
        event: Event instance with a to_sse() method.

    Returns:
        String in standard SSE format (event name + data payload).

    Raises:
        TypeError: If the event doesn't have a to_sse() method.
    """
    if not hasattr(event, "to_sse"):
        raise TypeError(f"Event {type(event)} does not have a to_sse() method")
    return event.to_sse()
