# SPEC.md — subagent-fleet

## Project

**Name:** `subagent-fleet`

**Repository:** `https://github.com/adityak74/subagent-fleet`

**Tagline:** "Local AI compute control plane for Claude Code and coding agents."

**One-line description:**  
`subagent-fleet` is a local AI compute control plane that routes coding subagents across your Macs, GPUs, and Ollama nodes — with real-time fleet health monitoring, role-based routing, model warmup, and execution tracing.

---

## 1. Product Vision

Modern coding agents increasingly use subagents for planning, implementation, review, testing, and summarization. Local model users often have multiple capable machines — MacBooks, Mac minis, GPU workstations, home servers — but their workflow usually still points to a single local Ollama endpoint.

`subagent-fleet` turns those machines into a private local subagent fleet.

Example:

```text
planner     → small fast model on M4 Mac mini 16GB
implementer → large coding model on M4 Mac mini 64GB
reviewer    → large coding model on M4 Mac mini 64GB
summarizer  → small local model on laptop
```

The tool should **not** replace Ollama or LiteLLM. It should sit above them as the control plane — managing routing, health monitoring, warmup, and observability.

---

## 2. Core Problem

Today, a developer can manually configure:

- Ollama on multiple machines
- LiteLLM proxy routing
- Claude Code subagent markdown files
- Environment variables for Claude Code
- Model warmup calls
- Health checks and status checks

But this is tedious and error-prone.

`subagent-fleet` should make this one config-driven workflow.

---

## 3. Non-Goals

This project is **not**:

- a new inference engine
- a replacement for Ollama
- a replacement for LiteLLM
- a model sharding framework
- Kubernetes for local LLMs
- a cloud orchestration platform
- a public model hosting tool

It should avoid overengineering.

The MVP should focus on:

- config
- discovery
- generation
- health checks
- warmup
- clear local developer workflow

---

## 4. Target Users

Primary users:

- developers using Claude Code or Claude-Code-like coding harnesses
- developers running Ollama locally
- people with multiple Macs/workstations
- local-first AI developers
- open-source builders trying to reduce cloud token usage
- privacy-conscious developers

---

## 5. MVP Scope

Implement a Python CLI named:

```bash
subagent-fleet
```

MVP commands:

```bash
subagent-fleet init
subagent-fleet discover
subagent-fleet validate
subagent-fleet generate
subagent-fleet warmup
subagent-fleet status
```

Optional but useful:

```bash
subagent-fleet doctor
subagent-fleet clean
```

Do **not** implement a daemon, dashboard, dynamic scheduler, or full proxy in the MVP.

---

## 6. Recommended Tech Stack

Use Python.

Suggested dependencies:

```text
typer          CLI framework
pydantic       config validation
pyyaml         YAML parsing/writing
httpx          HTTP calls to Ollama
jinja2         templates for generated files
rich           pretty terminal output
```

Suggested packaging:

```text
pyproject.toml
src/subagent_fleet/
```

---

## 7. Repository Structure

Create this structure:

```text
subagent-fleet/
  README.md
  SPEC.md
  LICENSE
  pyproject.toml
  .gitignore

  src/
    subagent_fleet/
      __init__.py
      cli.py
      config.py
      discovery.py
      health.py
      warmup.py
      status.py
      generators/
        __init__.py
        litellm.py
        claude_agents.py
        env_file.py
      templates/
        litellm_config.yaml.j2
        claude_agent.md.j2
        env.subagent-fleet.j2

  examples/
    fleet.yaml
    litellm_config.generated.yaml
    claude-agents/
      planner.md
      implementer.md
      reviewer.md

  tests/
    test_config.py
    test_discovery.py
    test_generate_litellm.py
    test_generate_claude_agents.py
```

---

## 8. Configuration File

Primary config file:

```text
fleet.yaml
```

The config should define:

- project metadata
- gateway settings
- Ollama nodes
- model aliases
- agent mappings

Example:

```yaml
project:
  name: local-dev
  gateway:
    provider: litellm
    host: 0.0.0.0
    port: 4000
    master_key_env: LITELLM_MASTER_KEY

nodes:
  m5-local:
    endpoint: http://localhost:11434
    tags:
      - controller
      - local
      - fast

  m4-mini-64gb:
    endpoint: http://192.168.1.50:11434
    tags:
      - heavy
      - coder
      - reviewer

  m4-mini-16gb:
    endpoint: http://192.168.1.51:11434
    tags:
      - small
      - planner
      - summarizer

models:
  heavy-coder:
    node: m4-mini-64gb
    ollama_model: qwen2.5-coder:32b
    litellm_alias: claude-sonnet-local
    context: 32768
    timeout: 600
    max_parallel: 1

  small-coder:
    node: m4-mini-16gb
    ollama_model: qwen2.5-coder:7b
    litellm_alias: claude-haiku-local
    context: 8192
    timeout: 300
    max_parallel: 1

agents:
  planner:
    model: small-coder
    description: Use for planning, file discovery, task decomposition, and summarization.
    tools:
      - Read
      - Grep
      - Glob
    prompt: |
      You are a fast local planning agent.
      Do not edit files.
      Return a concise response with:
      - plan
      - relevant files
      - risks
      - next recommended agent

  implementer:
    model: heavy-coder
    description: Use for implementation, bug fixes, refactors, and patch creation.
    tools:
      - Read
      - Grep
      - Glob
      - Edit
      - MultiEdit
      - Bash
    prompt: |
      You are a senior implementation agent.
      Make minimal, correct changes.
      Prefer small patches.
      Run relevant checks when possible.
      Explain what changed and why.

  reviewer:
    model: heavy-coder
    description: Use after implementation to review diffs, tests, regressions, and maintainability.
    tools:
      - Read
      - Grep
      - Glob
      - Bash
    prompt: |
      You are a strict code reviewer.
      Focus on correctness, regressions, missing tests, security issues,
      over-engineering, and maintainability.
      Review the diff and test output.
      Return only actionable issues.
```

---

## 9. Config Validation Rules

Validate `fleet.yaml` with Pydantic.

Rules:

### Project

- `project.name` required.
- `project.gateway.provider` defaults to `litellm`.
- `project.gateway.port` defaults to `4000`.
- `project.gateway.host` defaults to `127.0.0.1` unless explicitly set.

### Nodes

Each node must have:

```yaml
endpoint: http://host:port
```

Validation:

- endpoint must be valid HTTP/HTTPS URL.
- tags optional; default empty list.
- duplicate node names disallowed.

### Models

Each model must have:

- `node`
- `ollama_model`
- `litellm_alias`

Validation:

- `node` must reference existing `nodes` key.
- `context` default: `8192`.
- `timeout` default: `300`.
- `max_parallel` default: `1`.

### Agents

Each agent must have:

- `model`
- `description`

Validation:

- `model` must reference existing `models` key.
- `tools` defaults to `[]`.
- `prompt` defaults to a generic role prompt if omitted.
- agent names should be filesystem-safe: lowercase letters, numbers, hyphens, underscores.

---

## 10. CLI Command Details

### 10.1 `subagent-fleet init`

Creates a starter `fleet.yaml`.

Behavior:

- If `fleet.yaml` exists, do not overwrite unless `--force`.
- Generate a useful local example with:
  - local Ollama node
  - one heavy-coder model placeholder
  - planner, implementer, reviewer agents

Command:

```bash
subagent-fleet init
```

Options:

```bash
--force
--output fleet.yaml
```

Expected output:

```text
Created fleet.yaml
Edit it with your Ollama node endpoints, then run:

  subagent-fleet discover
  subagent-fleet generate
```

---

### 10.2 `subagent-fleet discover`

Discovers models available on configured Ollama nodes.

For each node:

Call:

```http
GET {node.endpoint}/api/tags
```

Expected Ollama response contains a `models` list.

Behavior:

- Load `fleet.yaml`.
- Check every node.
- Display online/offline status.
- Display discovered models.
- Optionally write discovery metadata to `.subagent-fleet/discovery.json`.

Command:

```bash
subagent-fleet discover
```

Options:

```bash
--config fleet.yaml
--json
--write
```

Expected terminal output:

```text
Fleet: local-dev

Node              Status   Models
-----------------------------------------------
m5-local          online   qwen-coder:14b, llama3.2:3b
m4-mini-64gb      online   qwen2.5-coder:32b
m4-mini-16gb      online   qwen2.5-coder:7b
```

Error handling:

- If a node fails, show it as offline.
- Do not crash the whole command unless config is invalid.
- Include connection error message in verbose mode.

---

### 10.3 `subagent-fleet validate`

Validates `fleet.yaml`.

Command:

```bash
subagent-fleet validate
```

Options:

```bash
--config fleet.yaml
```

Checks:

- config schema valid
- node references valid
- model references valid
- agent references valid
- endpoint format valid
- no duplicate aliases creating unintended collisions

Expected output:

```text
fleet.yaml is valid.
```

If invalid:

```text
Invalid fleet.yaml:

models.heavy-coder.node references unknown node: m4-mini-64
```

---

### 10.4 `subagent-fleet generate`

Generates:

```text
litellm_config.yaml
.claude/agents/*.md
.env.subagent-fleet
```

Command:

```bash
subagent-fleet generate
```

Options:

```bash
--config fleet.yaml
--out .
--litellm-only
--claude-only
--force
```

Behavior:

- Validate config first.
- Create output directories if missing.
- Do not overwrite generated files unless `--force`.
- Add a generated-file comment header.

Expected output:

```text
Generated:
  litellm_config.yaml
  .claude/agents/planner.md
  .claude/agents/implementer.md
  .claude/agents/reviewer.md
  .env.subagent-fleet
```

---

### 10.5 `subagent-fleet warmup`

Preloads configured Ollama models.

For each configured model:

Call:

```http
POST {node.endpoint}/api/chat
```

Payload:

```json
{
  "model": "qwen2.5-coder:32b",
  "messages": [],
  "keep_alive": -1
}
```

If Ollama does not accept empty `messages`, use a minimal warmup prompt:

```json
{
  "model": "qwen2.5-coder:32b",
  "messages": [
    {
      "role": "user",
      "content": "Reply with ok."
    }
  ],
  "stream": false,
  "keep_alive": -1
}
```

Command:

```bash
subagent-fleet warmup
```

Options:

```bash
--config fleet.yaml
--model heavy-coder
--agent implementer
```

Expected output:

```text
Warming models:

heavy-coder  m4-mini-64gb  qwen2.5-coder:32b  ok
small-coder  m4-mini-16gb  qwen2.5-coder:7b   ok
```

---

### 10.6 `subagent-fleet status`

Shows health/status of nodes and routes.

Command:

```bash
subagent-fleet status
```

Behavior:

- Validate config.
- Check `/api/tags` for every node.
- Optionally call `/api/ps` if available to show loaded models.
- Show agent routing table.

Expected output:

```text
Fleet: local-dev

Node              Status   Endpoint                    Models
---------------------------------------------------------------------------
m5-local          online   http://localhost:11434       qwen-coder:14b
m4-mini-64gb      online   http://192.168.1.50:11434    qwen2.5-coder:32b
m4-mini-16gb      online   http://192.168.1.51:11434    qwen2.5-coder:7b

Agent routing:

planner      -> m4-mini-16gb  -> qwen2.5-coder:7b   -> claude-haiku-local
implementer  -> m4-mini-64gb  -> qwen2.5-coder:32b  -> claude-sonnet-local
reviewer     -> m4-mini-64gb  -> qwen2.5-coder:32b  -> claude-sonnet-local
```

Options:

```bash
--json
--config fleet.yaml
```

---

## 11. Generated Files

### 11.1 Generated LiteLLM Config

Output file:

```text
litellm_config.yaml
```

Template output:

```yaml
# Generated by subagent-fleet.
# Do not edit manually unless you know what you are doing.

model_list:
{% for model_name, model in models.items() %}
  - model_name: {{ model.litellm_alias }}
    litellm_params:
      model: ollama_chat/{{ model.ollama_model }}
      api_base: {{ nodes[model.node].endpoint }}
      api_key: ollama
      timeout: {{ model.timeout }}
    model_info:
      max_input_tokens: {{ model.context }}
{% endfor %}

litellm_settings:
  drop_params: true
  master_key: os.environ/{{ project.gateway.master_key_env | default("LITELLM_MASTER_KEY") }}

router_settings:
  routing_strategy: simple-shuffle
  num_retries: 1
  timeout: 600
```

Important:

- Use `ollama_chat/` provider prefix for LiteLLM.
- Use `litellm_alias` as the exposed model name.
- Multiple models may share the same `litellm_alias` only if the user intentionally wants load balancing.
- Warn if multiple models share the same alias but point to different Ollama model names.

---

### 11.2 Generated Claude Code Agent Files

Output directory:

```text
.claude/agents/
```

For each agent, create:

```text
.claude/agents/{agent_name}.md
```

Template:

```markdown
---
name: {{ agent_name }}
description: {{ agent.description }}
model: {{ model.litellm_alias }}
tools: {{ agent.tools | join(", ") }}
---

{{ agent.prompt }}
```

Example:

```markdown
---
name: planner
description: Use for planning, file discovery, task decomposition, and summarization.
model: claude-haiku-local
tools: Read, Grep, Glob
---

You are a fast local planning agent.
Do not edit files.
Return a concise response with:
- plan
- relevant files
- risks
- next recommended agent
```

---

### 11.3 Generated Environment File

Output file:

```text
.env.subagent-fleet
```

Template:

```bash
# Generated by subagent-fleet.

export LITELLM_MASTER_KEY="${LITELLM_MASTER_KEY:-sk-local-dev}"

export ANTHROPIC_BASE_URL="http://localhost:{{ project.gateway.port }}"
export ANTHROPIC_AUTH_TOKEN="$LITELLM_MASTER_KEY"

{% if default_sonnet_model %}
export ANTHROPIC_DEFAULT_SONNET_MODEL="{{ default_sonnet_model }}"
{% endif %}

{% if default_haiku_model %}
export ANTHROPIC_DEFAULT_HAIKU_MODEL="{{ default_haiku_model }}"
{% endif %}
```

Also print usage:

```bash
source .env.subagent-fleet
claude
```

---

## 12. LiteLLM Launch Instructions

The generated output should include a terminal hint:

```bash
export LITELLM_MASTER_KEY="sk-local-dev"

litellm \
  --config ./litellm_config.yaml \
  --host 0.0.0.0 \
  --port 4000
```

If gateway host is `127.0.0.1`, use that instead.

---

## 13. Ollama Node Setup Instructions

README and/or CLI output should mention:

On each worker machine:

```bash
launchctl setenv OLLAMA_HOST "0.0.0.0:11434"
launchctl setenv OLLAMA_KEEP_ALIVE "-1"
launchctl setenv OLLAMA_NUM_PARALLEL "1"
launchctl setenv OLLAMA_MAX_LOADED_MODELS "1"

killall Ollama
open -a Ollama
```

Then from controller:

```bash
curl http://NODE_IP:11434/api/tags
```

Security warning:

Do not expose Ollama or LiteLLM to the public internet. Use LAN, firewall, Tailscale, or WireGuard.

---

## 14. Security Requirements

The tool should assume private local networking.

Warnings should appear in README and maybe `doctor` command:

- Do not expose Ollama directly to the public internet.
- Do not expose LiteLLM without authentication.
- Prefer Tailscale, WireGuard, or LAN.
- Use a non-default `LITELLM_MASTER_KEY` for anything beyond local dev.

The generated LiteLLM config should use:

```yaml
master_key: os.environ/LITELLM_MASTER_KEY
```

Never hardcode a real secret.

---

## 15. UX Principles

The CLI should feel practical and simple.

Good UX:

```bash
subagent-fleet init
subagent-fleet discover
subagent-fleet generate
subagent-fleet warmup
subagent-fleet status
```

Avoid making users manually understand every LiteLLM detail.

Make the output feel like:

```text
Your fleet is ready.
Planner goes to your small model.
Implementer goes to your big model.
Reviewer goes to your big model.
Claude Code can now connect to LiteLLM.
```

---

## 16. Recommended Defaults

Default roles:

```yaml
planner:
  small model
  tools: Read, Grep, Glob

summarizer:
  small model
  tools: Read

implementer:
  heavy model
  tools: Read, Grep, Glob, Edit, MultiEdit, Bash

reviewer:
  heavy model
  tools: Read, Grep, Glob, Bash
```

Default context:

```text
small model: 8192
heavy model: 32768
```

Default timeouts:

```text
small model: 300
heavy model: 600
```

Default max_parallel:

```text
1
```

Reason: local machines often hit VRAM/memory limits with parallel context buffers.

---

## 17. Implementation Details

### 17.1 Pydantic Models

Create models roughly like:

```python
class GatewayConfig(BaseModel):
    provider: str = "litellm"
    host: str = "127.0.0.1"
    port: int = 4000
    master_key_env: str = "LITELLM_MASTER_KEY"

class ProjectConfig(BaseModel):
    name: str
    gateway: GatewayConfig = GatewayConfig()

class NodeConfig(BaseModel):
    endpoint: AnyHttpUrl
    tags: list[str] = []

class ModelConfig(BaseModel):
    node: str
    ollama_model: str
    litellm_alias: str
    context: int = 8192
    timeout: int = 300
    max_parallel: int = 1

class AgentConfig(BaseModel):
    model: str
    description: str
    tools: list[str] = []
    prompt: str | None = None

class FleetConfig(BaseModel):
    project: ProjectConfig
    nodes: dict[str, NodeConfig]
    models: dict[str, ModelConfig]
    agents: dict[str, AgentConfig]
```

Add cross-field validation:

- model.node exists
- agent.model exists
- agent name valid
- optional duplicate alias warning

---

### 17.2 Discovery

Use `httpx.AsyncClient` or simple synchronous `httpx.Client`.

Function:

```python
def get_ollama_tags(endpoint: str, timeout: float = 5.0) -> list[str]:
    ...
```

Call:

```text
GET /api/tags
```

Return:

```python
["qwen2.5-coder:7b", "llama3.2:3b"]
```

Handle:

- connection refused
- timeout
- invalid JSON
- missing models key

---

### 17.3 Status

Status should combine:

- config routes
- node health
- discovered models

Optional call:

```text
GET /api/ps
```

If supported, show loaded/running models.

---

### 17.4 Generation

Use Jinja2 templates.

Functions:

```python
generate_litellm_config(config: FleetConfig, output_path: Path) -> None
generate_claude_agents(config: FleetConfig, output_dir: Path) -> None
generate_env_file(config: FleetConfig, output_path: Path) -> None
```

Do not overwrite unless force.

Add headers:

```yaml
# Generated by subagent-fleet.
# Source: fleet.yaml
```

For markdown:

```markdown
<!-- Generated by subagent-fleet. Source: fleet.yaml -->
```

---

## 18. Testing Requirements

### Unit Tests

Config tests:

- valid example config loads
- missing node reference fails
- missing model reference fails
- invalid URL fails
- default context applied
- default timeout applied

Generator tests:

- LiteLLM output contains `ollama_chat/model-name`
- LiteLLM output contains correct `api_base`
- Claude agent markdown has correct frontmatter
- environment file contains `ANTHROPIC_BASE_URL`

Discovery tests:

- mock `/api/tags`
- online node returns models
- offline node returns offline status without crashing

CLI tests:

- `init` creates `fleet.yaml`
- `validate` passes on example
- `generate` creates expected files in temp dir

---

## 19. Acceptance Criteria for MVP

MVP is complete when:

1. User can install the CLI locally.
2. User can run:

```bash
subagent-fleet init
```

3. User can edit `fleet.yaml`.
4. User can run:

```bash
subagent-fleet validate
```

5. User can run:

```bash
subagent-fleet discover
```

and see Ollama models from configured nodes.

6. User can run:

```bash
subagent-fleet generate
```

and receive:

```text
litellm_config.yaml
.claude/agents/*.md
.env.subagent-fleet
```

7. User can start LiteLLM using the generated config.
8. User can source the generated env file and run Claude Code.
9. Claude Code subagent files reference the generated LiteLLM aliases.
10. The README explains the local network security model.

---

## 20. Example First Implementation Plan

Build in this order:

### Step 1: package skeleton

- `pyproject.toml`
- `src/subagent_fleet/cli.py`
- basic Typer CLI
- `subagent-fleet --help`

### Step 2: config parser

- Pydantic models
- YAML loading
- `validate` command
- tests

### Step 3: init command

- write starter `fleet.yaml`
- do not overwrite by default

### Step 4: discovery

- call `/api/tags`
- display table
- support offline nodes gracefully

### Step 5: generators

- LiteLLM config generator
- Claude agents generator
- env file generator

### Step 6: warmup

- call `/api/chat`
- support all configured models
- show success/failure

### Step 7: status

- show nodes
- show model routes
- show agent routes

### Step 8: docs polish

- README examples
- security warning
- quickstart

---

## 21. Future Roadmap

After MVP:

```text
subagent-fleet benchmark
subagent-fleet recommend
subagent-fleet dashboard
subagent-fleet trace
```

Possible future features:

- latency benchmarking
- automatic role recommendation
- Tailscale-aware node discovery
- dynamic fallback models
- LiteLLM health/fallback generation
- model load monitoring
- Claude Code request tracing
- subagent execution trace viewer
- OpenAI-compatible harness examples
- support for vLLM, LM Studio, llama.cpp, OpenRouter, cloud APIs

---

## 22. Viral Demo Goal

The repo should support this demo:

```text
One Claude Code task.

Planner runs on Mac mini 16GB.
Implementer runs on Mac mini 64GB.
Reviewer runs on laptop or big node.

Terminal shows:
  planner     -> m4-mini-16gb  -> qwen-coder:7b
  implementer -> m4-mini-64gb  -> qwen-coder:32b
  reviewer    -> m4-mini-64gb  -> qwen-coder:32b

All local.
No cloud token burn.
```

Demo tagline:

```text
I turned 3 Macs into a private Claude Code subagent swarm.
```

---

## 23. README Positioning

Use this phrasing:

```text
Run Claude Code-style subagents across your local model fleet.
```

Avoid positioning as:

```text
distributed Ollama
```

because that sounds like model sharding and is already a crowded space.

Better:

```text
local subagent fleet manager
```

or:

```text
config-driven subagent orchestration for Ollama + LiteLLM
```

---

## 24. Important Design Principle

Prefer role-based routing over blind load balancing.

Good:

```text
planner     -> small model
implementer -> big coding model
reviewer    -> big coding model
summarizer  -> small model
```

Less useful for this project:

```text
send any request to any machine randomly
```

Load balancing only makes sense when the same model is loaded on multiple similar machines.

---

## 25. Final MVP Definition

The first release should be a small, reliable CLI that:

```text
reads fleet.yaml
checks Ollama nodes
generates LiteLLM config
generates Claude Code subagent files
warms models
shows status
```

Do not build a complex scheduler yet.

The value is making multi-machine local subagents easy, visible, and reproducible.
