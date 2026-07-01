# Fleet vs. Frontier Coding Eval — Design

## Goal

Show that the local subagent fleet (routed through the LiteLLM gateway) achieves
coding-task quality close to frontier models (Claude Sonnet 5, GPT-4o-mini via
OpenRouter), at effectively zero marginal cost, using an LLM judge for scoring.

## Architecture

New file: `tests/evals/test_frontier_comparison_live.py`, following the existing
`--run-live` pytest pattern in `tests/evals/conftest.py`.

- Gated behind `--run-live` AND a live `OPENROUTER_API_KEY` env var. If either is
  missing, the whole module skips cleanly — it must not break the existing
  482-test suite for anyone without a key.
- For each of 8 coding prompts, gather three responses:
  - **fleet**: call the LiteLLM gateway (`fleet.yaml` → `project.gateway.host:port`,
    default `http://0.0.0.0:4000`) using the `claude-sonnet-local` model alias
    (routes to `heavy-coder` / `qwen3-coder-next` on `mac-mini-64b`), OpenAI-compatible
    `/chat/completions`, `Authorization: Bearer $LITELLM_MASTER_KEY`.
  - **frontier-sonnet**: call OpenRouter chat completions with model id from
    `FRONTIER_MODEL_SONNET` env var (default constant, confirm actual OpenRouter
    slug once a key is available).
  - **frontier-gpt4o-mini**: call OpenRouter chat completions with model id from
    `FRONTIER_MODEL_GPT4OMINI` env var (default `openai/gpt-4o-mini`).
- A fourth OpenRouter call (Sonnet 5, same model id as above) acts as **judge**:
  given the original task + all three responses labeled A/B/C (label order
  randomized per prompt to avoid position bias), scores each independently
  0-10 and returns structured JSON.
- Latency (wall-clock request time) and cost are captured per response.
  - Fleet cost is a flat `$0.00` (documented assumption: local compute, no
    electricity/amortized-hardware accounting).
  - Frontier cost is pulled from OpenRouter's `GET /api/v1/generation?id=<id>`
    stats endpoint after each call (short retry loop — cost data lags slightly
    behind the completion), giving real `total_cost` in USD.
- Results collected into a scorecard, written to
  `tests/evals/reports/frontier_comparison.json`, and printed as a markdown
  summary table via `pytest -s` (score/latency/cost columns for fleet vs. each
  frontier model, plus an aggregate row) — same shape as the report already
  embedded in the README's "Verified With Evals" section.

## The 8 coding prompts

Each has an objectively checkable "correct" answer so the judge rubric has
real teeth:

1. Fix an off-by-one bug in a given binary search implementation.
2. Implement an LRU cache class with O(1) `get`/`put`.
3. Refactor a deeply-nested `if` function into early returns, preserving behavior.
4. Write pytest unit tests (including edge cases) for a given function.
5. Diagnose and fix a race condition in a given concurrent counter snippet.
6. Implement a token-bucket rate limiter class.
7. Rewrite a slow N+1-query pattern into a single JOIN (SQL + ORM code).
8. Implement a FastAPI endpoint handler from a given spec, with input validation.

## Judge rubric

Single rubric prompt per prompt/response-set. Judge sees the original task and
all three labeled (and order-randomized) responses. Scores each independently
0-10 on:

- **Correctness** (does it work / handle edge cases) — weighted heaviest
- **Code quality** (readability, idiomaticity)
- **Completeness** (does it fully address the ask)

Returns structured JSON: `{"A": {"score": x, "reasoning": "..."}, "B": {...}, "C": {...}}`.

## Pass bar

- Per-prompt: `fleet_score >= max(sonnet_score, gpt4o_mini_score) * 0.8`
- Aggregate: fleet's mean score across all 8 prompts is within 20% of the best
  frontier model's mean score.

## Out of scope

- Actual dollar accounting for local hardware/electricity (flat $0 assumption).
- Automated CI execution (requires a paid OpenRouter key + live 3-node fleet;
  stays in the `--run-live` opt-in bucket like the rest of `tests/evals/`).
- Multi-turn/agentic coding tasks (single-turn prompts only, matching the
  existing eval suite's style).
