# Subagent Fleet — Eval Suite

Eval categories for the `subagent-fleet` library. Each section lists what to assert and example prompts/inputs.

---

## 1. Fleet YAML Parsing & Validation

**What to test:** `load_fleet_config()` correctly parses valid configs, rejects bad ones, and surfaces actionable errors.

| Eval | Input | Expected |
|------|-------|----------|
| Valid 3-node cluster loads | `fleet.yaml` (examples/multi-node-cluster) | Parses without error, 4 agents, 4 models |
| Minimal fleet loads | Single node + one model + one agent | No error |
| Duplicate key rejected | Two `nodes:` keys in YAML | `ConfigError` with "duplicate key" message |
| Missing required field | `fleet.yaml` with no `project.name` | `ValidationError` |
| Invalid port | `gateway.port: 99999` | `ValidationError` |
| Bad agent name | Agent named `My Agent!` | Rejects — name must match `^[a-z0-9_-]+$` |
| Context too large | `context: 0` | `ValidationError` (ge=1) |
| Unknown extra field | `nodes.laptop.foo: bar` | `ConfigError` (extra=forbid) |
| Endpoint not a URL | `endpoint: not-a-url` | `ValidationError` |
| Cloud node without endpoint | `cloud_provider: aws`, no `endpoint` | Should succeed (endpoint is optional) |

**Example prompt for a model-graded eval:**
> "Given this fleet.yaml, list all model aliases that would be registered with LiteLLM: [paste fleet.yaml]"

---

## 2. Config Generation — LiteLLM

**What to test:** `generators/litellm.py` produces correct `litellm_config.yaml` from a parsed fleet.

| Eval | Input | Expected output |
|------|-------|-----------------|
| Alias mapping | `heavy-coder` → `ollama_model: qwen3-coder-next:latest`, node `mac-mini-64b` | Output has `model_name: claude-sonnet-local` pointing to `http://192.168.40.69:11434` |
| Timeout propagated | `timeout: 600` on model | LiteLLM config has `request_timeout: 600` |
| Max parallel respected | `max_parallel: 2` | `rpm_limit` or equivalent set to 2 |
| Context window set | `context: 65536` | `max_tokens` or context field = 65536 |
| Master key env written | `master_key_env: LITELLM_MASTER_KEY` | Config references `os.environ/LITELLM_MASTER_KEY` |
| Multi-node routing | 3 nodes, 4 models | Each model routes to correct node endpoint |

---

## 3. Config Generation — Claude Agents (AGENTS.md)

**What to test:** `generators/claude_agents.py` emits correct agent blocks.

| Eval | Input | Expected |
|------|-------|----------|
| Agent description preserved | `description: Use for planning...` | AGENTS.md block contains exact description |
| Tools list rendered | `tools: [Read, Grep, Glob]` | Agent block lists those three tools |
| Prompt injected | Custom `prompt:` in fleet.yaml | Prompt appears verbatim in AGENTS.md section |
| Read-only agent has no edit tools | `planner` agent (no Edit/Bash) | AGENTS.md block does not mention Edit, Write, Bash |
| Implementer has edit tools | `implementer` agent | Block lists Edit, MultiEdit, Bash |
| Model alias linked | `model: heavy-coder` | Agent block references `claude-sonnet-local` alias |

**Example prompt for a model-graded eval:**
> "Read this AGENTS.md and tell me: which agent should handle a code review task, and does it have write access to files? [paste generated AGENTS.md]"

---

## 4. Config Generation — Aider

**What to test:** `generators/aider.py` produces valid `.aider.conf.yml`.

| Eval | Input | Expected |
|------|-------|----------|
| Correct model string | `litellm_alias: claude-sonnet-local` | Aider config has `model: litellm/claude-sonnet-local` |
| API base points to gateway | `host: 0.0.0.0, port: 4000` | `api-base: http://0.0.0.0:4000` |
| Timeout set | `timeout: 600` | Written to aider config |

---

## 5. Node Discovery

**What to test:** `discovery.py` correctly probes Ollama nodes and reports health.

| Eval | Scenario | Expected |
|------|----------|----------|
| Healthy node detected | Mock Ollama at `localhost:11434` returns 200 | Node marked `healthy`, models listed |
| Unreachable node | Connection refused | Node marked `unreachable`, no crash |
| Partial cluster | 2 of 3 nodes online | Returns partial results, reports which are offline |
| Discovery cache written | First discovery run | Cache file created with timestamp |
| Cache used on second call | Cache exists and is fresh | No HTTP requests made, returns cached data |
| Cache invalidated | Cache older than TTL | Re-probes nodes |
| Model mismatch warning | Fleet declares `qwen3-coder-next:latest` but Ollama returns different models | Warning emitted, not a crash |

**Example prompts against your actual cluster:**
```
fleet discover
fleet status
fleet status --node mac-mini-64b
fleet status --node laptop
```

---

## 6. Agent Routing

**What to test:** `generators/router.py` selects the correct agent for a given task description.

| Eval | Input task | Expected agent |
|------|-----------|----------------|
| "Plan the migration from SQLite to Postgres" | planner task | `planner` (small-planner / gemma4) |
| "Fix the null pointer in auth.py line 42" | bug fix | `implementer` (heavy-coder / qwen3-coder-next) |
| "Review the diff for security issues" | code review | `reviewer` (heavy-coder) |
| "Summarize the 500-page spec doc" | large doc | `summarizer` if present, else best fit |
| Ambiguous task | "Do stuff" | Does not crash — returns a default or asks for clarification |
| Unknown task type | "Write a poem" | Either routes to a general agent or emits a clear "no suitable agent" message |

---

## 7. Warmup

**What to test:** `warmup.py` pings models and reports readiness.

| Eval | Scenario | Expected |
|------|----------|----------|
| All models warm | All nodes respond | `warmup complete` event broadcast via SSE |
| Partial warmup | 1 of 3 models fails | Partial success reported, failed model named |
| Warmup timeout | Model takes > `timeout` seconds | Marked as timed-out, not hung |
| Warmup progress events | SSE stream open during warmup | Progress events emitted per model (0–100%) |
| Retry on failure | First ping fails, second succeeds | Model eventually marked warm |

---

## 8. Dashboard / SSE

**What to test:** `ui/` server and SSE streaming behave correctly.

| Eval | Scenario | Expected |
|------|----------|----------|
| Dashboard starts | `fleet dashboard` | HTTP 200 on `/`, correct HTML |
| SSE endpoint open | `GET /events` | `Content-Type: text/event-stream` |
| Node health event | Node probe completes | `event: node_health` pushed on stream |
| Warmup progress event | Warmup running | `event: warmup_progress` pushed |
| Trace stream event | Agent call completes | `event: trace` pushed with metadata |
| Static file served | `GET /static/app.js` | 200, correct content-type |
| Path traversal blocked | `GET /static/../../../etc/passwd` | 400 or 404, not file contents |
| Reconnect on drop | Client disconnects and reconnects | Stream resumes without server crash |

---

## 9. CLI Surface

**What to test:** `cli.py` commands behave correctly end-to-end.

| Command | Scenario | Expected |
|---------|----------|----------|
| `fleet generate` | Valid `fleet.yaml` in cwd | Writes `litellm_config.yaml`, `AGENTS.md`, `.aider.conf.yml` |
| `fleet generate --out ./out` | Output dir flag | Files written to `./out/` |
| `fleet generate` | No `fleet.yaml` | Clear error: "fleet.yaml not found" |
| `fleet status` | Cluster reachable | Table with node/model/status |
| `fleet status --json` | JSON flag | Valid JSON output |
| `fleet warmup` | Nodes online | Exits 0 after all models warm |
| `fleet warmup --model heavy-coder` | Single model | Only warms that model |
| `fleet dashboard` | Default | Starts server on port 4000, prints URL |
| `fleet dashboard --port 5000` | Custom port | Starts on 5000 |
| `fleet --help` | No args | Prints usage without error |
| `fleet version` | | Prints semver string |

---

## 10. Security & Edge Cases

| Eval | Input | Expected |
|------|-------|----------|
| Endpoint injection | `endpoint: http://evil.com/../../passwd` | Rejected or safely escaped |
| Master key not set | `LITELLM_MASTER_KEY` env missing | Clear error, no crash |
| Zero-trust flag | `security.zero_trust_a2a: true` | Security config propagated to LiteLLM output |
| Very long agent prompt | 10,000 char prompt | Handled without truncation or crash |
| Empty agents block | `agents: {}` | Warning emitted, generates empty agent section |
| Duplicate model aliases | Two models with same `litellm_alias` | Error or dedup with warning |

---

## Your Actual Cluster — Live Smoke Tests

Using `fleet.yaml` in the repo root (3 nodes: `laptop`, `mac-mini-64b`, `mac-mini-16g`):

```bash
# Node reachability
fleet status --node laptop          # qwen3.6:35b-mlx @ localhost:11434
fleet status --node mac-mini-64b    # qwen3-coder-next:latest @ 192.168.40.69:11434
fleet status --node mac-mini-16g    # gemma4:latest @ 192.168.40.59:11434

# Model warmup
fleet warmup --model heavy-coder    # qwen3-coder-next on mac-mini-64b, timeout=600
fleet warmup --model small-planner  # gemma4 on mac-mini-16g, timeout=300
fleet warmup --model local-agent    # qwen3.6:35b-mlx on laptop, timeout=600

# Config generation round-trip
fleet generate
# Assert: litellm_config.yaml has 3 model_list entries
# Assert: claude-sonnet-local → 192.168.40.69:11434
# Assert: claude-haiku-local  → 192.168.40.59:11434
# Assert: claude-sonnet-local-alt → localhost:11434

# Agent routing smoke
fleet route "plan a refactor of the auth module"    # → planner
fleet route "fix the crash in discovery.py"         # → implementer
fleet route "review this diff for security holes"   # → reviewer
```

---

## Eval Scoring Rubric

For model-graded evals, use this rubric:

| Score | Meaning |
|-------|---------|
| 2 | Correct answer, correct reasoning |
| 1 | Correct answer, wrong or missing reasoning |
| 0 | Wrong answer |

For deterministic evals (CLI/parsing), use pass/fail with exit code + output assertions.
