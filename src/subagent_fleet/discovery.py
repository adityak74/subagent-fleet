from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from subagent_fleet.config import FleetConfig, NodeConfig


@dataclass(slots=True)
class NodeDiscovery:
    name: str
    endpoint: str
    online: bool
    models: list[str] = field(default_factory=list)
    loaded_models: list[str] = field(default_factory=list)
    error: str | None = None
    latency_ms: int | None = None


def get_ollama_tags(endpoint: str, timeout: float = 5.0) -> list[str]:
    with httpx.Client(timeout=timeout) as client:
        response = client.get(f"{endpoint.rstrip('/')}/api/tags")
        response.raise_for_status()
        payload = response.json()

    models = payload.get("models")
    if not isinstance(models, list):
        raise ValueError("Ollama /api/tags response is missing a models list")

    names: list[str] = []
    for item in models:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            names.append(item["name"])
        elif isinstance(item, str):
            names.append(item)
    return names


def get_loaded_models(endpoint: str, timeout: float = 5.0) -> list[str]:
    with httpx.Client(timeout=timeout) as client:
        response = client.get(f"{endpoint.rstrip('/')}/api/ps")
        response.raise_for_status()
        payload = response.json()

    models = payload.get("models")
    if not isinstance(models, list):
        return []
    loaded: list[str] = []
    for item in models:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            loaded.append(item["name"])
        elif isinstance(item, str):
            loaded.append(item)
    return loaded


def discover_node(name: str, node: NodeConfig, timeout: float = 5.0, include_loaded: bool = False) -> NodeDiscovery:
    if node.cloud_provider:
        return NodeDiscovery(name=name, endpoint="cloud", online=True, models=["*"])
    endpoint = node.endpoint_str
    try:
        start = httpx.Timeout(timeout)
        with httpx.Client(timeout=start) as client:
            response = client.get(f"{endpoint}/api/tags")
            response.read()
            try:
                elapsed = response.elapsed.total_seconds() if response.elapsed else None
            except RuntimeError:
                elapsed = None
            response.raise_for_status()
            payload = response.json()
        models = _parse_models(payload)
        loaded: list[str] = []
        if include_loaded:
            try:
                loaded = get_loaded_models(endpoint, timeout=timeout)
            except Exception:
                loaded = []
        return NodeDiscovery(
            name=name,
            endpoint=endpoint,
            online=True,
            models=models,
            loaded_models=loaded,
            latency_ms=int(elapsed * 1000) if elapsed is not None else None,
        )
    except Exception as exc:
        return NodeDiscovery(name=name, endpoint=endpoint, online=False, error=str(exc))


def discover_fleet(config: FleetConfig, timeout: float = 5.0, include_loaded: bool = False) -> list[NodeDiscovery]:
    return [
        discover_node(name, node, timeout=timeout, include_loaded=include_loaded)
        for name, node in config.nodes.items()
    ]


def discovery_to_json(results: list[NodeDiscovery]) -> list[dict[str, Any]]:
    return [
        {
            "name": result.name,
            "endpoint": result.endpoint,
            "status": "online" if result.online else "offline",
            "models": result.models,
            "loaded_models": result.loaded_models,
            "latency_ms": result.latency_ms,
            "error": result.error,
        }
        for result in results
    ]


def _parse_models(payload: dict[str, Any]) -> list[str]:
    models = payload.get("models")
    if not isinstance(models, list):
        raise ValueError("Ollama /api/tags response is missing a models list")
    names: list[str] = []
    for item in models:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            names.append(item["name"])
        elif isinstance(item, str):
            names.append(item)
    return names
