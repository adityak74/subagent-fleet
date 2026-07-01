"""EVALS - Fleet vs. Frontier Coding Comparison (live, opt-in).

Compares the local subagent fleet (via the LiteLLM gateway) against
Claude Sonnet 5 and GPT-4o-mini (via OpenRouter) on 8 coding tasks,
scored blind by an LLM judge (Sonnet 5 via OpenRouter).

Requires: --run-live AND OPENROUTER_API_KEY set. Also requires the live
3-node fleet + LiteLLM gateway to be running (see fleet.yaml).

Note: test_frontier_comparison_aggregate_report depends on _RESULTS being
populated by every test_frontier_comparison_prompt invocation, so this file
must be run in full without -k filtering or pytest-xdist parallelization.
"""

from __future__ import annotations

import hashlib
import os
import random
import time
from pathlib import Path

import httpx
import pytest

from .frontier_eval_lib import (
    PROMPTS,
    assign_labels,
    build_judge_prompt,
    fetch_generation_cost,
    format_markdown_table,
    parse_judge_response,
    write_json_report,
)

pytestmark = pytest.mark.live

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
FRONTIER_MODEL_SONNET = os.environ.get("FRONTIER_MODEL_SONNET", "anthropic/claude-sonnet-5")
FRONTIER_MODEL_GPT4OMINI = os.environ.get("FRONTIER_MODEL_GPT4OMINI", "openai/gpt-4o-mini")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", FRONTIER_MODEL_SONNET)
REPORT_PATH = Path(__file__).parent / "reports" / "frontier_comparison.json"

_RESULTS: list[dict] = []


def _call_openrouter(client: httpx.Client, model: str, prompt: str, api_key: str):
    start = time.time()
    resp = client.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}]},
        timeout=120.0,
    )
    latency = time.time() - start
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    generation_id = data.get("id", "")
    return content, latency, generation_id


def _call_fleet(client: httpx.Client, gateway_url: str, prompt: str):
    start = time.time()
    resp = client.post(
        f"{gateway_url}/chat/completions",
        headers={"Authorization": f"Bearer {os.environ.get('LITELLM_MASTER_KEY', 'sk-local-dev')}"},
        json={"model": "claude-sonnet-local", "messages": [{"role": "user", "content": prompt}]},
        timeout=180.0,
    )
    latency = time.time() - start
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return content, latency


@pytest.fixture(scope="session")
def gateway_url(live_fleet: dict) -> str:
    gw = live_fleet["project"]["gateway"]
    return f"http://{gw['host']}:{gw['port']}"


@pytest.fixture(scope="session")
def openrouter_client() -> httpx.Client:
    with httpx.Client() as client:
        yield client


@pytest.mark.parametrize("prompt_entry", PROMPTS, ids=[p["id"] for p in PROMPTS])
def test_frontier_comparison_prompt(
    prompt_entry, gateway_url, openrouter_client, openrouter_api_key
):
    """Fleet response scores within 20% of the best frontier model, per prompt."""
    task = prompt_entry["task"]

    fleet_content, fleet_latency = _call_fleet(openrouter_client, gateway_url, task)
    sonnet_content, sonnet_latency, sonnet_gen_id = _call_openrouter(
        openrouter_client, FRONTIER_MODEL_SONNET, task, openrouter_api_key
    )
    gpt_content, gpt_latency, gpt_gen_id = _call_openrouter(
        openrouter_client, FRONTIER_MODEL_GPT4OMINI, task, openrouter_api_key
    )

    sonnet_cost = fetch_generation_cost(openrouter_client, sonnet_gen_id, openrouter_api_key)
    gpt_cost = fetch_generation_cost(openrouter_client, gpt_gen_id, openrouter_api_key)

    names = ["fleet", "sonnet", "gpt4o_mini"]
    seed = int.from_bytes(hashlib.sha256(prompt_entry["id"].encode()).digest()[:4], "big")
    labels = assign_labels(names, random.Random(seed))
    contents = {"fleet": fleet_content, "sonnet": sonnet_content, "gpt4o_mini": gpt_content}
    labeled_responses = {labels[name]: contents[name] for name in names}

    judge_prompt = build_judge_prompt(task, labeled_responses)
    judge_raw, _judge_latency, _judge_gen_id = _call_openrouter(
        openrouter_client, JUDGE_MODEL, judge_prompt, openrouter_api_key
    )
    scores_by_label = parse_judge_response(judge_raw, list(labeled_responses.keys()))
    scores_by_name = {name: scores_by_label[labels[name]]["score"] for name in names}

    latencies = {"fleet": fleet_latency, "sonnet": sonnet_latency, "gpt4o_mini": gpt_latency}
    costs = {"fleet": 0.0, "sonnet": sonnet_cost, "gpt4o_mini": gpt_cost}

    for name in names:
        _RESULTS.append({
            "prompt_id": prompt_entry["id"],
            "system": name,
            "score": scores_by_name[name],
            "latency_s": latencies[name],
            "cost_usd": costs[name],
        })

    best_frontier = max(scores_by_name["sonnet"], scores_by_name["gpt4o_mini"])
    assert scores_by_name["fleet"] >= best_frontier * 0.8, (
        f"[{prompt_entry['id']}] fleet score {scores_by_name['fleet']} is below 80% "
        f"of best frontier score {best_frontier}"
    )


def test_frontier_comparison_aggregate_report(openrouter_api_key):
    """Aggregate: fleet's mean score is within 20% of the best frontier mean."""
    expected_result_count = len(PROMPTS) * 3
    if len(_RESULTS) != expected_result_count:
        pytest.skip(
            f"incomplete results: {len(_RESULTS)}/{expected_result_count} — "
            "run the full file without -k/-n filtering so all prompt tests populate _RESULTS"
        )

    write_json_report(_RESULTS, REPORT_PATH)
    table = format_markdown_table(_RESULTS)
    print("\n" + table)

    by_system: dict[str, list[float]] = {}
    for row in _RESULTS:
        by_system.setdefault(row["system"], []).append(row["score"])
    means = {system: sum(scores) / len(scores) for system, scores in by_system.items()}

    best_frontier_mean = max(means["sonnet"], means["gpt4o_mini"])
    assert means["fleet"] >= best_frontier_mean * 0.8, (
        f"fleet mean score {means['fleet']:.2f} is below 80% of best frontier "
        f"mean {best_frontier_mean:.2f}"
    )
