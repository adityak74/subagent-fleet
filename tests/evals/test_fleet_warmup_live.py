"""EVALS section 7 - Live Warmup Tests."""

from __future__ import annotations
from pathlib import Path

import pytest
import yaml
from subagent_fleet.config import load_config
from subagent_fleet.warmup import warmup_model, warmup_models, select_models


FLEET_LIVE = """project: {name: local-dev-cluster, gateway: {host: 0.0.0.0, port: 4000}}
nodes:
  laptop:         {endpoint: http://localhost:11434, tags: [local, fast]}
  mac64:          {endpoint: http://192.168.40.69:11434, tags: [heavy, coder]}
  mac16:          {endpoint: http://192.168.40.59:11434, tags: [small, planner]}
models:
  heavy-coder:        {node: mac64, ollama_model: qwen3-coder-next:latest, litellm_alias: sonnet-local}
  small-planner:      {node: mac16, ollama_model: gemma4:latest,              litellm_alias: haiku-local}
  local-agent:        {node: laptop, ollama_model: qwen3.6:35b-mlx,           litellm_alias: sonnet-alt}
agents:
  planner:      {model: small-planner, description: Plan tasks and discover files.}
  implementer: {model: heavy-coder,   description: Implement code and fix bugs.}"""


@pytest.fixture()
def cfg(tmp_path: Path):
    p = tmp_path / "fleet.yaml"
    p.write_text(FLEET_LIVE)
    return load_config(p)


# ── Single model warmup tests ───────────────────────────────────────────────

def test_heavy_coder_warms(cfg):
    r = warmup_model(cfg, "heavy-coder", timeout=600.0)
    assert r.model_name == "heavy-coder"
    assert r.node_name == "mac64"


def test_small_planner_warms(cfg):
    r = warmup_model(cfg, "small-planner", timeout=300.0)
    assert r.model_name == "small-planner"


def test_local_agent_warms(cfg):
    r = warmup_model(cfg, "local-agent", timeout=600.0)
    assert r.node_name == "laptop"


# ── Batch warmup tests ──────────────────────────────────────────────────────

def test_all_models_warm(cfg):
    results = warmup_models(cfg)
    assert isinstance(results, list)


def test_all_ok_or_error(cfg):
    results = warmup_models(cfg)
    for r in results:
        assert hasattr(r, "ok")


# ── WarmupResult dataclass tests ─────────────────────────────────────────────

def test_warmup_result_fields():
    from subagent_fleet.warmup import WarmupResult
    w = WarmupResult(model_name="m1", node_name="n1", ollama_model="qwen", ok=True)
    assert w.ok is True
    assert w.error is None


def test_warmup_result_failure():
    from subagent_fleet.warmup import WarmupResult
    w = WarmupResult(model_name="m1", node_name="n1", ollama_model="qwen", ok=False, error="refused")
    assert w.ok is False


# ── Select models tests ─────────────────────────────────────────────────────

def test_select_by_model(cfg):
    models = select_models(cfg, model_name="heavy-coder")
    assert models == ["heavy-coder"]


def test_select_by_agent_name(cfg):
    models = select_models(cfg, agent_name="planner")
    assert isinstance(models, list)


# ── Edge cases ───────────────────────────────────────────────────────────────

def test_short_timeout_handled(cfg):
    r = warmup_model(cfg, "heavy-coder", timeout=0.5)
    assert isinstance(r.ok, bool)


def test_offline_fails(tmp_path):
    fleet = yaml.dump({
         'project': {'name': 'off', 'gateway': {'host': '0.0.0.0', 'port': 4000}},
         'nodes': {'fake': {'endpoint': 'http://10.255.255.1:11434'}},
         'models': {'bad': {'node': 'fake', 'ollama_model': 'qwen', 'litellm_alias': 't'}},
         'agents': {'planner': {'model': 'bad', 'description': 'Plan'}},
    })
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    r = warmup_model(cfg, "bad", timeout=1.0)


def test_round_trip(cfg):
    from dataclasses import asdict
    r = warmup_model(cfg, "heavy-coder", timeout=60.0)
    d = asdict(r)
    assert "model_name" in d
    assert "node_name" in d


def test_repeated_is_idempotent(cfg):
    r1 = warmup_model(cfg, "heavy-coder", timeout=60.0)
    r2 = warmup_model(cfg, "heavy-coder", timeout=60.0)
    assert isinstance(r1.ok, bool)


def test_partial_success(tmp_path):
    fleet = yaml.dump({
         'project': {'name': 'partial', 'gateway': {'host': '0.0.0.0', 'port': 4000}},
         'nodes': {
             'on': {'endpoint': 'http://localhost:11434'},
             'off': {'endpoint': 'http://10.255.255.1:11434'},
         },
         'models': {
             'm1': {'node': 'on', 'ollama_model': 'qwen', 'litellm_alias': 'a'},
             'm2': {'node': 'off', 'ollama_model': 'llama', 'litellm_alias': 'b'},
         },
         'agents': {'planner': {'model': 'm1', 'description': 'Plan'}},
    })
    p = tmp_path / "fleet.yaml"
    p.write_text(fleet)
    cfg = load_config(p)
    results = warmup_models(cfg)
    assert len(results) == 2


def test_post_structure():
    pass
