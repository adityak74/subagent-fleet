# Fleet vs. Frontier Coding Eval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a live eval that compares the local subagent fleet against Sonnet 5 / GPT-4o-mini (via OpenRouter) on 8 coding tasks, scored by an LLM judge, producing a report showing near-frontier quality at near-zero cost.

**Architecture:** Pure logic (prompt dataset, judge-prompt building, judge-response parsing, cost-retrieval retry logic, report formatting) lives in `tests/evals/frontier_eval_lib.py` and is unit-tested with mocked HTTP (`tests/evals/test_frontier_eval_lib.py`, runs in the normal suite). Live network orchestration (calling the fleet gateway, OpenRouter frontier models, and the OpenRouter judge) lives in `tests/evals/test_frontier_comparison_live.py`, gated behind `--run-live` + a live `OPENROUTER_API_KEY`, following the existing `tests/evals/conftest.py` pattern.

**Tech Stack:** Python, pytest, httpx (existing project dependency).

## Global Constraints

- Follow existing eval file conventions: `tests/evals/*.py`, `@pytest.mark.live` on live tests, skip via `conftest.py`'s `pytest_runtest_setup` when `--run-live` is absent.
- No new third-party dependencies — use `httpx` (already used throughout `tests/evals/`).
- Fleet cost is a flat `$0.00` per response (documented assumption).
- Frontier model ids are overridable via env vars `FRONTIER_MODEL_SONNET` (default `anthropic/claude-sonnet-5`) and `FRONTIER_MODEL_GPT4OMINI` (default `openai/gpt-4o-mini`); judge model id is `JUDGE_MODEL` env var (default same as `FRONTIER_MODEL_SONNET`).
- Judge score scale: 0-10. Per-prompt pass bar: `fleet_score >= max(sonnet_score, gpt4o_mini_score) * 0.8`. Aggregate pass bar: fleet mean across all 8 prompts >= 80% of best frontier mean.

---

### Task 1: Prompt dataset

**Files:**
- Create: `tests/evals/frontier_eval_lib.py`
- Test: `tests/evals/test_frontier_eval_lib.py`

**Interfaces:**
- Produces: `PROMPTS: list[dict]` — each dict has keys `id: str`, `title: str`, `task: str`. Consumed by later tasks and by the live test file.

- [ ] **Step 1: Write the failing test**

```python
# tests/evals/test_frontier_eval_lib.py
"""Unit tests for frontier_eval_lib.py (no network calls)."""

from __future__ import annotations

from .frontier_eval_lib import PROMPTS


def test_prompts_dataset_has_eight_entries():
    assert len(PROMPTS) == 8


def test_prompts_dataset_ids_are_unique():
    ids = [p["id"] for p in PROMPTS]
    assert len(ids) == len(set(ids))


def test_prompts_dataset_entries_have_required_fields():
    for p in PROMPTS:
        assert isinstance(p["id"], str) and p["id"]
        assert isinstance(p["title"], str) and p["title"]
        assert isinstance(p["task"], str) and len(p["task"]) > 20
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/evals/test_frontier_eval_lib.py -v`
Expected: FAIL (ModuleNotFoundError / ImportError — `frontier_eval_lib` doesn't exist yet)

- [ ] **Step 3: Write the implementation**

Create `tests/evals/frontier_eval_lib.py`:

```python
"""Pure-logic helpers for the fleet-vs-frontier coding eval.

No network I/O in this module — see test_frontier_comparison_live.py for
the live orchestration that calls the fleet gateway and OpenRouter.
"""

from __future__ import annotations

PROMPTS: list[dict] = [
    {
        "id": "binary_search_off_by_one",
        "title": "Fix off-by-one bug in binary search",
        "task": (
            "This binary search has an off-by-one bug that makes it miss the "
            "last element of the array. Find and fix the bug. Return only the "
            "corrected Python code.\n\n"
            "```python\n"
            "def binary_search(arr, target):\n"
            "    lo, hi = 0, len(arr) - 1\n"
            "    while lo < hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            lo = mid + 1\n"
            "        else:\n"
            "            hi = mid - 1\n"
            "    return -1\n"
            "```"
        ),
    },
    {
        "id": "lru_cache",
        "title": "Implement an LRU cache",
        "task": (
            "Implement a Python class LRUCache(capacity: int) with O(1) get(key) "
            "and put(key, value) methods. get returns -1 if the key is missing. "
            "When capacity is exceeded, evict the least-recently-used entry. "
            "Return only the Python code."
        ),
    },
    {
        "id": "refactor_nested_ifs",
        "title": "Refactor nested ifs into early returns",
        "task": (
            "Refactor this function to use early returns instead of nested ifs, "
            "preserving its exact behavior. Return only the refactored Python code.\n\n"
            "```python\n"
            "def classify(age, has_license, has_car):\n"
            "    if age >= 18:\n"
            "        if has_license:\n"
            "            if has_car:\n"
            "                return 'can drive own car'\n"
            "            else:\n"
            "                return 'can drive, no car'\n"
            "        else:\n"
            "            return 'needs license'\n"
            "    else:\n"
            "        return 'too young'\n"
            "```"
        ),
    },
    {
        "id": "pytest_unit_tests",
        "title": "Write pytest unit tests with edge cases",
        "task": (
            "Write pytest unit tests (including edge cases like empty input and "
            "negative numbers) for this function. Return only the test code.\n\n"
            "```python\n"
            "def clamp(value, lo, hi):\n"
            "    return max(lo, min(value, hi))\n"
            "```"
        ),
    },
    {
        "id": "race_condition_fix",
        "title": "Diagnose and fix a race condition",
        "task": (
            "This counter class has a race condition when incremented from "
            "multiple threads. Diagnose the bug and return corrected Python "
            "code that is thread-safe.\n\n"
            "```python\n"
            "class Counter:\n"
            "    def __init__(self):\n"
            "        self.value = 0\n"
            "\n"
            "    def increment(self):\n"
            "        self.value = self.value + 1\n"
            "```"
        ),
    },
    {
        "id": "token_bucket_rate_limiter",
        "title": "Implement a token-bucket rate limiter",
        "task": (
            "Implement a Python class TokenBucket(rate: float, capacity: int) "
            "with a method allow() -> bool that returns True if a request is "
            "allowed under the token-bucket algorithm (refilling `rate` tokens "
            "per second, capped at `capacity`), False otherwise. Return only "
            "the Python code."
        ),
    },
    {
        "id": "n_plus_1_to_join",
        "title": "Rewrite N+1 query pattern into a JOIN",
        "task": (
            "This SQLAlchemy code has an N+1 query problem: it issues one query "
            "per author to fetch their books. Rewrite it to use a single query "
            "with a JOIN (or eager loading). Return only the corrected Python code.\n\n"
            "```python\n"
            "authors = session.query(Author).all()\n"
            "for author in authors:\n"
            "    books = session.query(Book).filter(Book.author_id == author.id).all()\n"
            "    print(author.name, [b.title for b in books])\n"
            "```"
        ),
    },
    {
        "id": "fastapi_endpoint",
        "title": "Implement a FastAPI endpoint with validation",
        "task": (
            "Implement a FastAPI POST endpoint `/users` that accepts JSON body "
            "{name: str, email: str, age: int}, validates that age >= 0 and "
            "email contains '@' (return HTTP 422 if invalid), and returns the "
            "created user with a generated integer id. Return only the Python code."
        ),
    },
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/evals/test_frontier_eval_lib.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add tests/evals/frontier_eval_lib.py tests/evals/test_frontier_eval_lib.py
git commit -m "test: add coding-task prompt dataset for frontier comparison eval"
```

---

### Task 2: Label randomization + judge prompt builder

**Files:**
- Modify: `tests/evals/frontier_eval_lib.py`
- Modify: `tests/evals/test_frontier_eval_lib.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `assign_labels(names: list[str], rng: random.Random) -> dict[str, str]` — maps each name (e.g. `"fleet"`, `"sonnet"`, `"gpt4o_mini"`) to a shuffled single-letter label (`"A"`, `"B"`, `"C"`). Consumed by Task 6.
  - `build_judge_prompt(task: str, labeled_responses: dict[str, str]) -> str` — `labeled_responses` maps label (`"A"`/`"B"`/`"C"`) to response text. Returns the full judge rubric prompt string. Consumed by Task 6.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/evals/test_frontier_eval_lib.py
import random

from .frontier_eval_lib import assign_labels, build_judge_prompt


def test_assign_labels_maps_every_name_to_unique_label():
    labels = assign_labels(["fleet", "sonnet", "gpt4o_mini"], random.Random(42))
    assert set(labels.keys()) == {"fleet", "sonnet", "gpt4o_mini"}
    assert set(labels.values()) == {"A", "B", "C"}


def test_assign_labels_is_deterministic_for_same_seed():
    labels1 = assign_labels(["fleet", "sonnet", "gpt4o_mini"], random.Random(1))
    labels2 = assign_labels(["fleet", "sonnet", "gpt4o_mini"], random.Random(1))
    assert labels1 == labels2


def test_build_judge_prompt_includes_task_and_all_labeled_responses():
    prompt = build_judge_prompt(
        "Write a function that adds two numbers.",
        {"A": "def add(a, b): return a + b", "B": "def add(a,b):\n    return a-b"},
    )
    assert "Write a function that adds two numbers." in prompt
    assert "def add(a, b): return a + b" in prompt
    assert "def add(a,b):\n    return a-b" in prompt
    assert "Response A" in prompt
    assert "Response B" in prompt
    assert "JSON" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/evals/test_frontier_eval_lib.py -v -k "assign_labels or build_judge_prompt"`
Expected: FAIL (ImportError — names don't exist yet)

- [ ] **Step 3: Write the implementation**

Append to `tests/evals/frontier_eval_lib.py`:

```python
import random


def assign_labels(names: list[str], rng: random.Random) -> dict[str, str]:
    """Shuffle names onto letter labels A, B, C... to avoid judge position bias."""
    letters = [chr(ord("A") + i) for i in range(len(names))]
    shuffled_letters = letters[:]
    rng.shuffle(shuffled_letters)
    return dict(zip(names, shuffled_letters))


def build_judge_prompt(task: str, labeled_responses: dict[str, str]) -> str:
    """Build the rubric prompt sent to the judge model.

    labeled_responses maps a letter label ("A", "B", ...) to that
    response's text. Labels are pre-shuffled by assign_labels so the judge
    never learns which system produced which response.
    """
    responses_block = "\n\n".join(
        f"Response {label}:\n{text}"
        for label, text in sorted(labeled_responses.items())
    )
    labels_list = ", ".join(f'"{l}"' for l in sorted(labeled_responses.keys()))
    return (
        "You are grading responses to a coding task. Score each response "
        "0-10 on:\n"
        "- Correctness (does it work / handle edge cases) — weighted heaviest\n"
        "- Code quality (readability, idiomaticity)\n"
        "- Completeness (does it fully address the ask)\n\n"
        f"Task:\n{task}\n\n"
        f"{responses_block}\n\n"
        "Return ONLY a JSON object mapping each label to its score and a "
        "one-sentence reasoning, in this exact shape (no other text):\n"
        "{" + ", ".join(
            f'"{l}": {{"score": <0-10 number>, "reasoning": "<one sentence>"}}'
            for l in sorted(labeled_responses.keys())
        ) + "}\n"
        f"Labels to score: {labels_list}"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/evals/test_frontier_eval_lib.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 5: Commit**

```bash
git add tests/evals/frontier_eval_lib.py tests/evals/test_frontier_eval_lib.py
git commit -m "feat: add label randomization and judge prompt builder"
```

---

### Task 3: Judge response parser

**Files:**
- Modify: `tests/evals/frontier_eval_lib.py`
- Modify: `tests/evals/test_frontier_eval_lib.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `parse_judge_response(raw_text: str, expected_labels: list[str]) -> dict[str, dict]` — returns `{label: {"score": float, "reasoning": str}}` for each expected label. Raises `ValueError` if a label is missing or the score isn't a number in [0, 10]. Consumed by Task 6.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/evals/test_frontier_eval_lib.py
import pytest

from .frontier_eval_lib import parse_judge_response


def test_parse_judge_response_extracts_scores_and_reasoning():
    raw = '{"A": {"score": 8, "reasoning": "Correct and clean."}, "B": {"score": 3.5, "reasoning": "Buggy."}}'
    result = parse_judge_response(raw, ["A", "B"])
    assert result["A"]["score"] == 8.0
    assert result["A"]["reasoning"] == "Correct and clean."
    assert result["B"]["score"] == 3.5


def test_parse_judge_response_handles_surrounding_prose():
    raw = 'Here is my evaluation:\n{"A": {"score": 7, "reasoning": "ok"}}\nThanks.'
    result = parse_judge_response(raw, ["A"])
    assert result["A"]["score"] == 7.0


def test_parse_judge_response_raises_on_missing_label():
    raw = '{"A": {"score": 7, "reasoning": "ok"}}'
    with pytest.raises(ValueError):
        parse_judge_response(raw, ["A", "B"])


def test_parse_judge_response_raises_on_out_of_range_score():
    raw = '{"A": {"score": 15, "reasoning": "ok"}}'
    with pytest.raises(ValueError):
        parse_judge_response(raw, ["A"])


def test_parse_judge_response_raises_on_unparseable_text():
    with pytest.raises(ValueError):
        parse_judge_response("not json at all", ["A"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/evals/test_frontier_eval_lib.py -v -k parse_judge_response`
Expected: FAIL (ImportError)

- [ ] **Step 3: Write the implementation**

Append to `tests/evals/frontier_eval_lib.py`:

```python
import json
import re


def parse_judge_response(raw_text: str, expected_labels: list[str]) -> dict[str, dict]:
    """Extract {label: {"score": float, "reasoning": str}} from the judge's raw text.

    Tolerates surrounding prose by extracting the first {...} block.
    """
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in judge response: {raw_text!r}")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Judge response is not valid JSON: {raw_text!r}") from exc

    result: dict[str, dict] = {}
    for label in expected_labels:
        if label not in data:
            raise ValueError(f"Judge response missing label {label!r}: {data!r}")
        entry = data[label]
        score = float(entry["score"])
        if not (0 <= score <= 10):
            raise ValueError(f"Judge score for {label!r} out of range [0,10]: {score}")
        result[label] = {"score": score, "reasoning": str(entry.get("reasoning", ""))}
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/evals/test_frontier_eval_lib.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 5: Commit**

```bash
git add tests/evals/frontier_eval_lib.py tests/evals/test_frontier_eval_lib.py
git commit -m "feat: add judge response parser with validation"
```

---

### Task 4: OpenRouter cost-retrieval helper

**Files:**
- Modify: `tests/evals/frontier_eval_lib.py`
- Modify: `tests/evals/test_frontier_eval_lib.py`

**Interfaces:**
- Consumes: `httpx.Client`-like object (duck-typed, `.get(url, headers=...)` returning an object with `.status_code` and `.json()`).
- Produces: `fetch_generation_cost(client, generation_id: str, api_key: str, *, max_attempts: int = 5, sleep_fn=time.sleep) -> float` — polls `https://openrouter.ai/api/v1/generation?id=<id>` until `total_cost` is present, returns it as float; returns `0.0` if it never becomes available after `max_attempts`. Consumed by Task 6.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/evals/test_frontier_eval_lib.py
from .frontier_eval_lib import fetch_generation_cost


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def get(self, url, headers=None):
        self.calls += 1
        return self._responses.pop(0)


def test_fetch_generation_cost_returns_cost_when_available():
    client = _FakeClient([
        _FakeResponse(200, {"data": {"total_cost": 0.0042}}),
    ])
    cost = fetch_generation_cost(client, "gen-123", "fake-key", sleep_fn=lambda s: None)
    assert cost == 0.0042
    assert client.calls == 1


def test_fetch_generation_cost_retries_until_cost_present():
    client = _FakeClient([
        _FakeResponse(404, {}),
        _FakeResponse(200, {"data": {"total_cost": 0.001}}),
    ])
    cost = fetch_generation_cost(client, "gen-123", "fake-key", sleep_fn=lambda s: None)
    assert cost == 0.001
    assert client.calls == 2


def test_fetch_generation_cost_gives_up_after_max_attempts():
    client = _FakeClient([_FakeResponse(404, {}) for _ in range(5)])
    cost = fetch_generation_cost(
        client, "gen-123", "fake-key", max_attempts=5, sleep_fn=lambda s: None
    )
    assert cost == 0.0
    assert client.calls == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/evals/test_frontier_eval_lib.py -v -k fetch_generation_cost`
Expected: FAIL (ImportError)

- [ ] **Step 3: Write the implementation**

Append to `tests/evals/frontier_eval_lib.py`:

```python
import time


def fetch_generation_cost(
    client,
    generation_id: str,
    api_key: str,
    *,
    max_attempts: int = 5,
    sleep_fn=time.sleep,
) -> float:
    """Poll OpenRouter's generation stats endpoint for the real USD cost.

    Cost data can lag slightly behind the completion, so this retries with
    a short delay between attempts. Returns 0.0 if cost is never available.
    """
    url = f"https://openrouter.ai/api/v1/generation?id={generation_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    for attempt in range(max_attempts):
        resp = client.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            if "total_cost" in data:
                return float(data["total_cost"])
        if attempt < max_attempts - 1:
            sleep_fn(1.0)
    return 0.0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/evals/test_frontier_eval_lib.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 5: Commit**

```bash
git add tests/evals/frontier_eval_lib.py tests/evals/test_frontier_eval_lib.py
git commit -m "feat: add OpenRouter generation cost polling helper"
```

---

### Task 5: Report formatting (JSON + markdown table)

**Files:**
- Modify: `tests/evals/frontier_eval_lib.py`
- Modify: `tests/evals/test_frontier_eval_lib.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `ScoreRow = dict` shape: `{"prompt_id": str, "system": str, "score": float, "latency_s": float, "cost_usd": float}`.
  - `format_markdown_table(rows: list[ScoreRow]) -> str` — one row per `(prompt_id, system)`, plus an aggregate section per system (mean score, mean latency, total cost).
  - `write_json_report(rows: list[ScoreRow], path: pathlib.Path) -> None` — writes `{"rows": rows, "aggregate": {...}}` as JSON.
  Consumed by Task 6.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/evals/test_frontier_eval_lib.py
import json as json_module

from .frontier_eval_lib import format_markdown_table, write_json_report

_SAMPLE_ROWS = [
    {"prompt_id": "p1", "system": "fleet", "score": 8.0, "latency_s": 2.1, "cost_usd": 0.0},
    {"prompt_id": "p1", "system": "sonnet", "score": 9.0, "latency_s": 1.5, "cost_usd": 0.01},
    {"prompt_id": "p2", "system": "fleet", "score": 7.0, "latency_s": 2.5, "cost_usd": 0.0},
    {"prompt_id": "p2", "system": "sonnet", "score": 8.5, "latency_s": 1.7, "cost_usd": 0.012},
]


def test_format_markdown_table_includes_all_rows_and_aggregate():
    table = format_markdown_table(_SAMPLE_ROWS)
    assert "p1" in table and "p2" in table
    assert "fleet" in table and "sonnet" in table
    assert "Aggregate" in table


def test_write_json_report_writes_rows_and_aggregate(tmp_path):
    out_path = tmp_path / "report.json"
    write_json_report(_SAMPLE_ROWS, out_path)
    data = json_module.loads(out_path.read_text())
    assert data["rows"] == _SAMPLE_ROWS
    assert "fleet" in data["aggregate"]
    assert data["aggregate"]["fleet"]["mean_score"] == 7.5
    assert data["aggregate"]["fleet"]["total_cost_usd"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/evals/test_frontier_eval_lib.py -v -k "format_markdown_table or write_json_report"`
Expected: FAIL (ImportError)

- [ ] **Step 3: Write the implementation**

Append to `tests/evals/frontier_eval_lib.py`:

```python
import pathlib
from collections import defaultdict


def _aggregate_by_system(rows: list[dict]) -> dict[str, dict]:
    by_system: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_system[row["system"]].append(row)
    aggregate = {}
    for system, system_rows in by_system.items():
        aggregate[system] = {
            "mean_score": sum(r["score"] for r in system_rows) / len(system_rows),
            "mean_latency_s": sum(r["latency_s"] for r in system_rows) / len(system_rows),
            "total_cost_usd": sum(r["cost_usd"] for r in system_rows),
        }
    return aggregate


def format_markdown_table(rows: list[dict]) -> str:
    lines = [
        "| Prompt | System | Score | Latency (s) | Cost (USD) |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['prompt_id']} | {row['system']} | {row['score']:.1f} | "
            f"{row['latency_s']:.2f} | ${row['cost_usd']:.4f} |"
        )
    lines.append("")
    lines.append("**Aggregate**")
    lines.append("")
    lines.append("| System | Mean Score | Mean Latency (s) | Total Cost (USD) |")
    lines.append("|---|---|---|---|")
    for system, agg in _aggregate_by_system(rows).items():
        lines.append(
            f"| {system} | {agg['mean_score']:.2f} | {agg['mean_latency_s']:.2f} | "
            f"${agg['total_cost_usd']:.4f} |"
        )
    return "\n".join(lines)


def write_json_report(rows: list[dict], path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"rows": rows, "aggregate": _aggregate_by_system(rows)}
    path.write_text(json.dumps(payload, indent=2))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/evals/test_frontier_eval_lib.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 5: Commit**

```bash
git add tests/evals/frontier_eval_lib.py tests/evals/test_frontier_eval_lib.py
git commit -m "feat: add markdown/JSON report formatting for frontier eval"
```

---

### Task 6: Live orchestration test file

**Files:**
- Create: `tests/evals/test_frontier_comparison_live.py`
- Modify: `tests/evals/conftest.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `PROMPTS`, `assign_labels`, `build_judge_prompt`, `parse_judge_response`, `fetch_generation_cost`, `format_markdown_table`, `write_json_report` from `tests/evals/frontier_eval_lib.py` (Tasks 1-5). Also consumes `live_fleet` fixture from `conftest.py` (existing) for gateway host/port.
- Produces: pytest tests `test_frontier_comparison_prompt[<prompt_id>]` (parametrized) and `test_frontier_comparison_aggregate_report`, plus `tests/evals/reports/frontier_comparison.json` as a side effect when run live.

- [ ] **Step 1: Add an `openrouter_api_key` skip fixture to conftest.py**

In `tests/evals/conftest.py`, add near the other fixtures:

```python
import os


@pytest.fixture(scope="session")
def openrouter_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        pytest.skip("OPENROUTER_API_KEY not set — skipping frontier comparison eval")
    return key
```

- [ ] **Step 2: Add reports directory to .gitignore**

Append to `.gitignore`:

```
tests/evals/reports/
```

- [ ] **Step 3: Write the live test file**

Create `tests/evals/test_frontier_comparison_live.py`:

```python
"""EVALS - Fleet vs. Frontier Coding Comparison (live, opt-in).

Compares the local subagent fleet (via the LiteLLM gateway) against
Claude Sonnet 5 and GPT-4o-mini (via OpenRouter) on 8 coding tasks,
scored blind by an LLM judge (Sonnet 5 via OpenRouter).

Requires: --run-live AND OPENROUTER_API_KEY set. Also requires the live
3-node fleet + LiteLLM gateway to be running (see fleet.yaml).
"""

from __future__ import annotations

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
    labels = assign_labels(names, random.Random(hash(prompt_entry["id"]) % (2**32)))
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
    if not _RESULTS:
        pytest.skip("no per-prompt results collected — run test_frontier_comparison_prompt first")

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
```

- [ ] **Step 4: Verify the file imports cleanly (no live network yet)**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -c "import tests.evals.test_frontier_comparison_live"`
Expected: no output, exit code 0 (import succeeds; no network call happens at import time)

- [ ] **Step 5: Verify it skips cleanly without --run-live and without a key**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/evals/test_frontier_comparison_live.py -v`
Expected: all tests SKIPPED (no `--run-live` passed)

- [ ] **Step 6: Verify the full unit suite still passes**

Run: `cd /Users/adityakarnam/Projects/subagent-fleet && python -m pytest tests/ -v --ignore=tests/evals/test_frontier_comparison_live.py -k "not live"`
Expected: all existing tests PASS (no regressions), plus the new `test_frontier_eval_lib.py` tests pass

- [ ] **Step 7: Commit**

```bash
git add tests/evals/test_frontier_comparison_live.py tests/evals/conftest.py .gitignore
git commit -m "feat: add live fleet-vs-frontier coding comparison eval"
```

---

## Post-plan note (out of scope for this plan, left for the user)

Once a real `OPENROUTER_API_KEY` is available, run:

```bash
export OPENROUTER_API_KEY=<key>
export LITELLM_MASTER_KEY=<key>  # must match fleet.yaml's master_key_env target
litellm --config ./litellm_config.yaml &  # gateway must be running
cd /Users/adityakarnam/Projects/subagent-fleet
python -m pytest tests/evals/test_frontier_comparison_live.py --run-live -v -s
```

Confirm the actual OpenRouter model slugs for Sonnet 5 (`FRONTIER_MODEL_SONNET`) match
what's live on OpenRouter at run time — override via env var if the default constant
is stale. Paste the printed markdown table (or `tests/evals/reports/frontier_comparison.json`)
into the README's "Verified With Evals" section if you want to publish the results.
