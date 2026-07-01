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
