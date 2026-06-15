---
name: subagent-fleet-operations
description: Use and troubleshoot an existing generated subagent fleet.
---

# subagent-fleet operations

Use this skill when a user already has generated `subagent-fleet` files and wants to run, inspect, update, or troubleshoot the fleet.

## Generated Files

Expected generated files:

- `litellm_config.yaml`
- `.claude/agents/*.md`
- `.env.subagent-fleet`
- optionally `.subagent-fleet/discovery.json`

These files should contain generated-file headers. Avoid hand-editing generated files when the source change belongs in `fleet.yaml`.

## Runbook

Validate config:

```bash
subagent-fleet validate
```

Discover models:

```bash
subagent-fleet discover --json
```

Generate outputs:

```bash
subagent-fleet generate --force
```

Warm a specific model:

```bash
subagent-fleet warmup --model heavy-coder
```

Warm the model used by a specific agent:

```bash
subagent-fleet warmup --agent implementer
```

Show status and routes:

```bash
subagent-fleet status
```

Show safety and worker setup guidance:

```bash
subagent-fleet doctor
```

## Routing Model

Agents reference configured model keys. Models reference Ollama nodes and expose LiteLLM aliases.

```text
agent -> model key -> Ollama node + Ollama model -> LiteLLM alias
```

Prefer role-based routing:

- planning and summarization to small/fast models
- implementation and review to larger coding models

## Troubleshooting

- If generated Claude agent files point to the wrong model, inspect `agents.<agent>.model` and `models.<model>.litellm_alias`.
- If LiteLLM cannot connect, inspect `models.<model>.node` and `nodes.<node>.endpoint`.
- If Ollama rejects warmup, retry with a normal prompt or verify the model is pulled on that node.
- If a generated file already exists, rerun with `--force` only when overwriting is intentional.
