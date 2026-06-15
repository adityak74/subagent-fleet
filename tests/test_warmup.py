from __future__ import annotations

import json

import httpx

from subagent_fleet.config import load_config
from subagent_fleet.warmup import warmup_model, warmup_models


def test_warmup_model_posts_empty_messages(monkeypatch) -> None:
    config = load_config("tests/fixtures/fleet.yaml")
    seen_payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_payloads.append(json.loads(request.content.decode()))
        return httpx.Response(200, json={"message": {"content": "ok"}})

    transport = httpx.MockTransport(handler)

    class MockClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "Client", MockClient)

    result = warmup_model(config, "small-coder")

    assert result.ok is True
    assert result.ollama_model == "qwen2.5-coder:7b"
    assert seen_payloads == [
        {
            "model": "qwen2.5-coder:7b",
            "messages": [],
            "stream": False,
            "keep_alive": -1,
        }
    ]


def test_warmup_falls_back_to_minimal_prompt(monkeypatch) -> None:
    config = load_config("tests/fixtures/fleet.yaml")
    calls = 0
    bodies: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        bodies.append(request.content.decode())
        if calls == 1:
            return httpx.Response(400, json={"error": "messages required"})
        return httpx.Response(200, json={"message": {"content": "ok"}})

    transport = httpx.MockTransport(handler)

    class MockClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "Client", MockClient)

    result = warmup_model(config, "small-coder")

    assert result.ok is True
    assert calls == 2
    assert '"messages":[]' in bodies[0]
    assert "Reply with ok." in bodies[1]


def test_warmup_selects_agent_model(monkeypatch) -> None:
    config = load_config("tests/fixtures/fleet.yaml")

    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"message": {"content": "ok"}}))

    class MockClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "Client", MockClient)

    results = warmup_models(config, agent_name="planner")

    assert [result.model_name for result in results] == ["small-coder"]
