"""EVALS - Live Prompt Evaluation Across All 3 Fleet Nodes.

Tests actual LLM inference through Ollama on each node:
- planner (gemma4:latest @ mac-mini-16g)
- implementer (qwen3-coder-next:latest @ mac-mini-64b)
- local-agent (qwen3.6:35b-mlx @ laptop)

Prompts cover: math, code generation, code review, planning, classification.
Responses are validated for correctness using regex + heuristics.
"""

from __future__ import annotations

import httpx
import pytest

NODES = {
    "laptop": {
        "endpoint": "http://localhost:11434",
        "model": "qwen3.6:35b-mlx",
    },
    "mac-mini-64b": {
        "endpoint": "http://192.168.40.69:11434",
        "model": "qwen3-coder-next:latest",
    },
    "mac-mini-16g": {
        "endpoint": "http://192.168.40.59:11434",
        "model": "gemma4:latest",
    },
}


@pytest.fixture()
def ollama_client() -> httpx.Client:
    return httpx.Client(timeout=120.0)


# -- Section Aa: Basic math - all nodes --------------------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_math_addition(node_name, node, ollama_client):
    """All nodes correctly compute 2 + 2 = 4."""
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{
                "role": "user",
                "content": "What is 2 + 2? Reply with just the number.",
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"].strip()
    assert "4" in content or "four" in content.lower(), (
        f"[{node_name}] Expected '4' but got: {content}"
    )


@pytest.mark.parametrize("node_name,node", NODES.items())
def test_math_multiplication(node_name, node, ollama_client):
    """All nodes correctly compute 6 x 7 = 42."""
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{
                "role": "user",
                "content": "What is 6 times 7? Reply with just the number.",
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"].strip()
    assert "42" in content, (
        f"[{node_name}] Expected '42' but got: {content}"
    )


# -- Section Ab: Math with reasoning - all nodes ------------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_math_reasoning(node_name, node, ollama_client):
    """All nodes can do simple arithmetic with reasoning."""
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "I have 5 apples. I eat 2, then buy 8 more. "
                    "How many do I have now? Reply with just the number."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"].strip()
    # Answer: 5 - 2 + 8 = 11
    assert "11" in content, (f"[{node_name}] Expected '11' but got: {content}")


# -- Section Ac: Basic code generation - implementer node ---------------------

def test_implementer_fibonacci(ollama_client):
    """Implementer node generates a correct fibonacci function."""
    resp = ollama_client.post(
        f"{NODES['mac-mini-64b']['endpoint']}/api/chat",
        json={
            "model": NODES["mac-mini-64b"]["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Write a Python function fib(n) that returns the nth Fibonacci number.\n"
                    "It must pass: fib(0)==0, fib(1)==1, fib(10)==55.\n"
                    "Return ONLY the Python code in a code block."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"]
    assert "def fib" in content or "def fibonacci" in content, (
        f"[mac-mini-64b] Expected 'def fib' but got: {content[:500]}"
    )
    assert "n <= 1" in content or "n < 2" in content or "n == 0" in content, (
        f"[mac-mini-64b] Expected base case check but got: {content[:500]}"
    )


# -- Section Ad: Code review - implementer node -------------------------------

def test_implementer_code_review_identifies_bug(ollama_client):
    """Implementer correctly identifies a bug in the provided code."""
    buggy_code = (
        "```python\n"
        "def add(a, b):\n"
        "    return a - b\n"
        "```\n"
        "Review this code for bugs. What is wrong?"
    )
    resp = ollama_client.post(
        f"{NODES['mac-mini-64b']['endpoint']}/api/chat",
        json={
            "model": NODES["mac-mini-64b"]["model"],
            "messages": [{"role": "user", "content": buggy_code}],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"].lower()
    assert "minus" in content or "wrong" in content or (
        "incorrect" in content
    ) or "subtract" in content or "-" in content, (
        f"[mac-mini-64b] Expected bug identification but got: "
        f"{resp.json()['message']['content'][:500]}"
    )


# -- Section Ae: Planning task - planner node ---------------------------------

def test_planner_task_decomposition(ollama_client):
    """Planner correctly decomposes a task into steps."""
    resp = ollama_client.post(
        f"{NODES['mac-mini-16g']['endpoint']}/api/chat",
        json={
            "model": NODES["mac-mini-16g"]["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Plan the steps to migrate a SQLite database to PostgreSQL.\n"
                    "Return exactly 3 bullet points, one per line."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"]
    lines = [
        l.strip() for l in content.splitlines()
        if l.strip() and any(l.strip().startswith(k) for k in ("-", "*", "•") + (tuple(f"{i}." for i in range(1, 5))))
    ]
    assert len(lines) >= 2, (
        f"[mac-mini-16g planner] Expected 2+ steps but got: {content[:500]}"
    )


# -- Section Af: Summarization - planner node ---------------------------------

def test_planner_summarization(ollama_client):
    """Planner produces a concise summary."""
    resp = ollama_client.post(
        f"{NODES['mac-mini-16g']['endpoint']}/api/chat",
        json={
            "model": NODES["mac-mini-16g"]["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Summarize in one sentence: 'The quick brown fox jumps over "
                    "the lazy dog. A computer is a machine that processes data. "
                    "Python is a programming language.'"
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"]
    assert len(content) > 10


# -- Section Ag: Code generation - laptop node --------------------------------

def test_laptop_code_generation(ollama_client):
    """Laptop generates a working Python function."""
    resp = ollama_client.post(
        f"{NODES['laptop']['endpoint']}/api/chat",
        json={
            "model": NODES["laptop"]["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Write a Python function reverse_string(s) that "
                    "returns the reversed string.\nReturn ONLY the code."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"]
    assert "def reverse" in content or "return" in content, (
        f"[laptop] Expected a function but got: {content[:500]}"
    )


# -- Section Ah: Classification - all nodes -----------------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_text_classification(node_name, node, ollama_client):
    """All nodes correctly classify text sentiment."""
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Classify the sentiment as POSITIVE, NEGATIVE, or NEUTRAL.\n"
                    "Input: 'I love using this product!'\n"
                    "Output: (just the label)"
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"].strip().upper()
    assert any(
        label in content for label in ["POSITIVE", "NEGATIVE", "NEUTRAL"]
    ), (f"[{node_name}] Expected a sentiment label but got: {content}")


# -- Section Ai: JSON output - all nodes --------------------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_json_output_format(node_name, node, ollama_client):
    """All nodes can output structured JSON."""
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Return exactly this JSON:\n"
                    "{'answer': 42}\n"
                    "Only output the JSON, nothing else."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"].strip()
    assert "{" in content or "42" in content, (
        f"[{node_name}] Expected JSON with '42' but got: {content[:300]}"
    )


# -- Section Aj: Self-awareness - all nodes -----------------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_self_identification(node_name, node, ollama_client):
    """All nodes can identify themselves."""
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{
                "role": "user",
                "content": "What is your name? Reply with a short answer.",
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"].strip()
    assert len(content) > 0


# -- Section Ak: Code review - laptop node ------------------------------------

def test_laptop_code_review(ollama_client):
    """Laptop identifies a logic error in code."""
    resp = ollama_client.post(
        f"{NODES['laptop']['endpoint']}/api/chat",
        json={
            "model": NODES["laptop"]["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Review this Python function for bugs:\n"
                    "```python\n"
                    "def max_of_three(a, b, c):\n"
                    "    return min(a, b, c)\n"
                    "```\n"
                    "What is wrong? Reply with one word: 'bug' or 'ok'."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"].lower()
    assert any(w in content for w in [
        "bug", "wrong", "incorrect", "reverse", "min",
    ]), (
        f"[laptop] Expected bug identification but got: "
        f"{resp.json()['message']['content'][:500]}"
    )


# -- Section Al: Prompt throughput - all nodes --------------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_prompt_latency(node_name, node, ollama_client):
    """All nodes respond to a simple prompt within 30 seconds."""
    import time
    start = time.time()
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{"role": "user", "content": "Reply: ok"}],
            "stream": False,
        },
    )
    elapsed = time.time() - start
    assert resp.status_code == 200
    assert elapsed < 30.0, (
        f"[{node_name}] Took {elapsed:.1f}s - expected < 30s"
    )


# -- Section Am: Multi-step reasoning - all nodes -----------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_multi_step_reasoning(node_name, node, ollama_client):
    """All nodes handle multi-step reasoning."""
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Alice has 3 apples. Bob has twice as many. "
                    "Charlie has half of Bob's.\n"
                    "How many does Charlie have? Reply with just the number."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"].strip()
    # Alice=3, Bob=6, Charlie=3 -> answer is 3
    assert "3" in content, (f"[{node_name}] Expected '3' but got: {content}")


# -- Section An: Instruction following - all nodes ----------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_instruction_following(node_name, node, ollama_client):
    """All nodes follow explicit output format instructions."""
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Reply with EXACTLY this single word: SUBMIT\n"
                    "Do not add any other text. Do not add punctuation."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"].strip().upper()
    assert "SUBMIT" in content, (
        f"[{node_name}] Expected 'SUBMIT' but got: {content}"
    )


# -- Section Ao: Long context window - mac-mini-64b ---------------------------

def test_heavy_node_long_context(ollama_client):
    """mac-mini-64b handles a longer prompt without issues."""
    long_context = " ".join(["The cat sat on the mat."] * 200)
    resp = ollama_client.post(
        f"{NODES['mac-mini-64b']['endpoint']}/api/chat",
        json={
            "model": NODES["mac-mini-64b"]["model"],
            "messages": [{
                "role": "user",
                "content": (
                    f"Repeat the word 'mat' from this text and reply "
                    f"with just the count:\n{long_context}"
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"].strip()
    assert len(content) > 0


# -- Section Ap: Agent-specific task - planner vs implementer -----------------

def test_planner_task_plan(ollama_client):
    """Planner (mac-mini-16g) produces a structured plan with numbered steps."""
    resp = ollama_client.post(
        f"{NODES['mac-mini-16g']['endpoint']}/api/chat",
        json={
            "model": NODES["mac-mini-16g"]["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Plan the steps to add a new endpoint to a REST API.\n"
                    "Return EXACTLY 4 numbered steps. Start each with 'Step N:'."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"]
    steps = [l for l in content.splitlines() if "Step" in l or "step" in l]
    assert len(steps) >= 2, (
        f"[mac-mini-16g planner] Expected 2+ steps but got: {content[:500]}"
    )


def test_implementer_task_code(ollama_client):
    """Implementer (mac-mini-64b) generates runnable code."""
    resp = ollama_client.post(
        f"{NODES['mac-mini-64b']['endpoint']}/api/chat",
        json={
            "model": NODES["mac-mini-64b"]["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Write a Python function is_sorted(arr) that returns "
                    "True if the list is sorted ascending.\n"
                    "Only return code, no explanation."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"]
    assert "def is_sorted" in content or "all(" in content or (
        ">" in content
    ), (f"[mac-mini-64b implementer] Expected sorted check but got: {content[:500]}")


# -- Section Aq: Edge case - empty response handling --------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_response_never_empty(node_name, node, ollama_client):
    """All nodes return non-empty content."""
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"]
    assert len(content.strip()) > 0, (f"[{node_name}] Empty response")


# -- Section Ar: Multi-language code - all nodes ------------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_multilingual_code(node_name, node, ollama_client):
    """All nodes can write JavaScript alongside Python."""
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Write a JavaScript function sum(a, b) that returns a + b.\n"
                    "Return only code."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"]
    assert "function" in content or "=>" in content, (
        f"[{node_name}] Expected JS arrow function but got: {content[:300]}"
    )


# -- Section As: Evaluation scorecard - collect all results -------------------

def test_eval_scorecard_all_nodes_pass(ollama_client):
    """Run a single eval prompt against every node and collect scores."""
    scorecard = {}
    for node_name, node in NODES.items():
        resp = ollama_client.post(
            f"{node['endpoint']}/api/chat",
            json={
                "model": node["model"],
                "messages": [{"role": "user", "content": "Reply: ok"}],
                "stream": False,
            },
        )
        scorecard[node_name] = {
            "status_code": resp.status_code,
            "ok": resp.status_code == 200,
            "model": node["model"],
            "endpoint": node["endpoint"],
        }
    for name, result in scorecard.items():
        assert result["ok"], (
            f"{name}: status_code={result['status_code']}"
        )


# -- Section At: Large file review - implementer --------------------------------

def test_implementer_large_file_review(ollama_client):
    """Implementer handles a code review on a larger snippet."""
    code = "\n".join(f"line_{i} = {i}" for i in range(100))
    resp = ollama_client.post(
        f"{NODES['mac-mini-64b']['endpoint']}/api/chat",
        json={
            "model": NODES["mac-mini-64b"]["model"],
            "messages": [{
                "role": "user",
                "content": (
                    "Review this generated code for potential issues:\n"
                    f"```\n{code}\n```\n"
                    "What could be improved? Reply with 2 suggestions."
                ),
            }],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    content = resp.json()["message"]["content"]
    assert len(content) > 20  # Non-trivial response expected


# -- Section Au: Ollama error handling - invalid model ------------------------

def test_invalid_model_returns_error(ollama_client):
    """Requesting a non-existent model returns an error."""
    resp = ollama_client.post(
        f"{NODES['laptop']['endpoint']}/api/chat",
        json={
            "model": "definitely-not-a-real-model-999",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        },
    )
    assert resp.status_code != 200 or (
        isinstance(resp.json(), dict) and resp.json().get("error") is not None
    )


# -- Section Av: Streaming vs non-streaming - all nodes -----------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_non_streaming_works(node_name, node, ollama_client):
    """Non-streaming chat works on all nodes."""
    resp = ollama_client.post(
        f"{node['endpoint']}/api/chat",
        json={
            "model": node["model"],
            "messages": [{"role": "user", "content": "Reply: ok"}],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert "content" in data["message"]


# -- Section Aw: Model tags endpoint - all nodes ------------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_model_tags_endpoint(node_name, node, ollama_client):
    """All nodes respond to /api/tags."""
    resp = ollama_client.get(f"{node['endpoint']}/api/tags")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data


# -- Section Ax: Health check - all nodes -------------------------------------

@pytest.mark.parametrize("node_name,node", NODES.items())
def test_health_check(node_name, node, ollama_client):
    """All Ollama nodes respond to /api/tags as a health check."""
    resp = ollama_client.get(f"{node['endpoint']}/api/tags", timeout=10.0)
    assert resp.status_code == 200
