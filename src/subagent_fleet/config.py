from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

AGENT_NAME_RE = re.compile(r"^[a-z0-9_-]+$")
DEFAULT_AGENT_PROMPT = "You are a local subagent. Follow the agent description and return a concise, useful response."


class ConfigError(ValueError):
    """Raised when fleet.yaml cannot be loaded or validated."""


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key: {key}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


class GatewayConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = "litellm"
    host: str = "127.0.0.1"
    port: int = Field(default=4000, ge=1, le=65535)
    master_key_env: str = "LITELLM_MASTER_KEY"


class SecurityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zero_trust_a2a: bool = False


class ObservabilityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    langfuse: bool = False
    langsmith: bool = False
    opentelemetry: bool = False


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    dynamic_routing: bool = False


class NodeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint: AnyHttpUrl | None = None
    cloud_provider: str | None = None
    provider: str = "ollama"
    tags: list[str] = Field(default_factory=list)
    wake_on_lan: str | None = None

    @property
    def endpoint_str(self) -> str:
        return str(self.endpoint).rstrip("/") if self.endpoint else ""


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node: str
    ollama_model: str
    litellm_alias: str
    context: int = Field(default=8192, gt=0)
    timeout: int = Field(default=300, gt=0)
    max_parallel: int = Field(default=1, gt=0)
    fallback: str | None = None
    context_pool: str | None = None


class McpServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

class McpServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    description: str
    tools: list[str] = Field(default_factory=list)
    prompt: str | None = None

    @field_validator("prompt")
    @classmethod
    def default_prompt(cls, value: str | None) -> str:
        if value is None or not value.strip():
            return DEFAULT_AGENT_PROMPT
        return value


class FleetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project: ProjectConfig
    nodes: dict[str, NodeConfig]
    models: dict[str, ModelConfig]
    agents: dict[str, AgentConfig]
    mcp_servers: dict[str, McpServerConfig] = Field(default_factory=dict)
    mcp_servers: dict[str, McpServerConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_references(self) -> "FleetConfig":
        for node_name in self.nodes:
            if not node_name:
                raise ValueError("node names must not be empty")

        for model_name, model in self.models.items():
            if model.node not in self.nodes:
                raise ValueError(f"models.{model_name}.node references unknown node: {model.node}")
            if model.fallback and model.fallback not in self.models:
                raise ValueError(f"models.{model_name}.fallback references unknown model: {model.fallback}")
            if model.fallback and model.fallback not in self.models:
                raise ValueError(f"models.{model_name}.fallback references unknown model: {model.fallback}")
            if model.fallback and model.fallback not in self.models:
                raise ValueError(f"models.{model_name}.fallback references unknown model: {model.fallback}")

        for agent_name, agent in self.agents.items():
            if not AGENT_NAME_RE.fullmatch(agent_name):
                raise ValueError(
                    f"agents.{agent_name} must be filesystem-safe: lowercase letters, numbers, hyphens, underscores"
                )
            if agent.model not in self.models:
                raise ValueError(f"agents.{agent_name}.model references unknown model: {agent.model}")

        return self

    def alias_warnings(self) -> list[str]:
        aliases: dict[str, set[str]] = {}
        for model in self.models.values():
            aliases.setdefault(model.litellm_alias, set()).add(model.ollama_model)
        return [
            f"alias {alias!r} is used for multiple Ollama models: {', '.join(sorted(models))}"
            for alias, models in sorted(aliases.items())
            if len(models) > 1
        ]


def load_config(path: Path | str) -> FleetConfig:
    config_path = Path(path)
    try:
        raw = yaml.load(config_path.read_text(), Loader=UniqueKeyLoader) or {}
    except FileNotFoundError as exc:
        raise ConfigError(f"{config_path} does not exist") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"{config_path} is not valid YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"{config_path} must contain a YAML mapping")

    try:
        return FleetConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(format_validation_error(exc)) from exc
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc


def format_validation_error(exc: ValidationError) -> str:
    errors: list[str] = []
    for error in exc.errors():
        loc = ".".join(str(part) for part in error["loc"])
        msg = error["msg"]
        errors.append(f"{loc}: {msg}" if loc else msg)
    return "\n".join(errors)


def config_to_plain_dict(config: FleetConfig) -> dict[str, Any]:
    return config.model_dump(mode="json")
