---
name: subagent-fleet-setup
description: Set up, validate, generate, and verify a local subagent fleet.
---

# subagent-fleet setup

Use this skill when a user wants to set up or change a local `subagent-fleet` configuration for Claude Code-style subagents, Ollama nodes, and LiteLLM routing.

## Goal

Help the user create a working private local subagent fleet:

- `fleet.yaml` validates.
- Ollama nodes are reachable or clearly reported offline.
- LiteLLM config is generated.
- Assistant agent files are generated.
- Environment variables are generated.
- The user knows how to start LiteLLM and connect their coding assistant.

## Workflow

1. Inspect the repository for `fleet.yaml`, `pyproject.toml`, `README.md`, and generated outputs.
2. If there is no `fleet.yaml`, run:

```bash
subagent-fleet init
```

3. Ask the user for real Ollama endpoints and model names only if they are not discoverable from existing files.
4. Validate the config:

```bash
subagent-fleet validate
```

5. Discover configured Ollama nodes:

```bash
subagent-fleet discover --verbose
```

Offline nodes are not automatically fatal. Report which nodes failed and why.

6. Generate files:

```bash
subagent-fleet generate
```

Use `--force` only after confirming overwriting generated files is intended.

7. Show the user the next commands:

```bash
export LITELLM_MASTER_KEY="sk-local-dev"
litellm --config ./litellm_config.yaml --host 127.0.0.1 --port 4000
source .env.subagent-fleet
```

8. Verify routing:

```bash
subagent-fleet status
```

## Safety

Do not expose Ollama or LiteLLM to the public internet. Prefer LAN, firewall rules, Tailscale, WireGuard, or a private subnet. Do not commit real secrets.

## Common Fixes

- Unknown model reference: update `agents.<name>.model` to an existing key under `models`.
- Unknown node reference: update `models.<name>.node` to an existing key under `nodes`.
- Duplicate LiteLLM alias warning: confirm whether the user intended load balancing.
- Offline node: check `OLLAMA_HOST`, firewall rules, machine IP, and `curl http://NODE_IP:11434/api/tags`.
