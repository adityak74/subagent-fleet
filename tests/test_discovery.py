from __future__ import annotations

import httpx

from subagent_fleet.config import load_config
from subagent_fleet.discovery import discover_node, get_ollama_tags


def test_get_ollama_tags_parses_models() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"models": [{"name": "qwen:7b"}]}))

    original_client = httpx.Client

    class MockClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=transport, **kwargs)

    httpx.Client = MockClient
    try:
        assert get_ollama_tags("http://localhost:11434") == ["qwen:7b"]
    finally:
        httpx.Client = original_client


def test_discover_node_offline_does_not_crash() -> None:
    config = load_config("tests/fixtures/fleet.yaml")
    node = config.nodes["local"]

    result = discover_node("local", node, timeout=0.001)

    assert result.name == "local"
    assert result.online is False
    assert result.error


def test_discover_node_online_returns_models(monkeypatch) -> None:
    config = load_config("tests/fixtures/fleet.yaml")
    node = config.nodes["local"]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": [{"name": "llama3.2:3b"}, {"name": "qwen:7b"}]})

    transport = httpx.MockTransport(handler)

    class MockClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "Client", MockClient)

    result = discover_node("local", node)

    assert result.online is True
    assert result.models == ["llama3.2:3b", "qwen:7b"]
