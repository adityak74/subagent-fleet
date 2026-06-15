STARTER_FLEET_YAML = """project:
  name: local-dev
  gateway:
    provider: litellm
    host: 127.0.0.1
    port: 4000
    master_key_env: LITELLM_MASTER_KEY

nodes:
  local-ollama:
    endpoint: http://localhost:11434
    tags:
      - controller
      - local
      - fast

models:
  heavy-coder:
    node: local-ollama
    ollama_model: qwen2.5-coder:32b
    litellm_alias: claude-sonnet-local
    context: 32768
    timeout: 600
    max_parallel: 1

  small-coder:
    node: local-ollama
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
"""
