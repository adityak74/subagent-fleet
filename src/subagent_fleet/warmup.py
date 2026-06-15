from __future__ import annotations

from dataclasses import dataclass

import httpx

from subagent_fleet.config import FleetConfig


@dataclass(slots=True)
class WarmupResult:
    model_name: str
    node_name: str
    ollama_model: str
    ok: bool
    error: str | None = None


def select_models(config: FleetConfig, model_name: str | None = None, agent_name: str | None = None) -> list[str]:
    if model_name and agent_name:
        raise ValueError("Use either --model or --agent, not both")
    if model_name:
        if model_name not in config.models:
            raise ValueError(f"unknown model: {model_name}")
        return [model_name]
    if agent_name:
        if agent_name not in config.agents:
            raise ValueError(f"unknown agent: {agent_name}")
        return [config.agents[agent_name].model]
    return list(config.models)


def warmup_model(config: FleetConfig, model_name: str, timeout: float | None = None) -> WarmupResult:
    model = config.models[model_name]
    node = config.nodes[model.node]
    payload = {
        "model": model.ollama_model,
        "messages": [],
        "stream": False,
        "keep_alive": -1,
    }
    client_timeout = timeout if timeout is not None else model.timeout
    try:
        with httpx.Client(timeout=client_timeout) as client:
            response = client.post(f"{node.endpoint_str}/api/chat", json=payload)
            if response.status_code >= 400:
                fallback = {
                    "model": model.ollama_model,
                    "messages": [{"role": "user", "content": "Reply with ok."}],
                    "stream": False,
                    "keep_alive": -1,
                }
                response = client.post(f"{node.endpoint_str}/api/chat", json=fallback)
            response.raise_for_status()
        return WarmupResult(model_name=model_name, node_name=model.node, ollama_model=model.ollama_model, ok=True)
    except Exception as exc:
        return WarmupResult(
            model_name=model_name,
            node_name=model.node,
            ollama_model=model.ollama_model,
            ok=False,
            error=str(exc),
        )


def warmup_models(config: FleetConfig, model_name: str | None = None, agent_name: str | None = None) -> list[WarmupResult]:
    return [warmup_model(config, selected) for selected in select_models(config, model_name, agent_name)]
