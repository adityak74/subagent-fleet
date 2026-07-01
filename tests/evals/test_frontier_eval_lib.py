"""Unit tests for frontier_eval_lib.py (no network calls)."""

from __future__ import annotations

import random

from .frontier_eval_lib import PROMPTS, assign_labels, build_judge_prompt


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
