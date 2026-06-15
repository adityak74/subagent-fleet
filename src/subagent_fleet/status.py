from __future__ import annotations

from dataclasses import dataclass

from subagent_fleet.config import FleetConfig
from subagent_fleet.discovery import NodeDiscovery, discover_fleet


@dataclass(slots=True)
class AgentRoute:
    agent: str
    node: str
    ollama_model: str
    litellm_alias: str


def get_agent_routes(config: FleetConfig) -> list[AgentRoute]:
    routes: list[AgentRoute] = []
    for agent_name, agent in config.agents.items():
        model = config.models[agent.model]
        routes.append(
            AgentRoute(
                agent=agent_name,
                node=model.node,
                ollama_model=model.ollama_model,
                litellm_alias=model.litellm_alias,
            )
        )
    return routes


def get_status(config: FleetConfig, timeout: float = 5.0) -> tuple[list[NodeDiscovery], list[AgentRoute]]:
    return discover_fleet(config, timeout=timeout, include_loaded=True), get_agent_routes(config)


def routes_to_json(routes: list[AgentRoute]) -> list[dict[str, str]]:
    return [
        {
            "agent": route.agent,
            "node": route.node,
            "ollama_model": route.ollama_model,
            "litellm_alias": route.litellm_alias,
        }
        for route in routes
    ]
