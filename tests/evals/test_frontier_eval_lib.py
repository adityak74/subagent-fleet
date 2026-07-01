"""Unit tests for frontier_eval_lib.py (no network calls)."""

from __future__ import annotations

import pytest
import random

from .frontier_eval_lib import (
    PROMPTS,
    assign_labels,
    build_judge_prompt,
    parse_judge_response,
)


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


def test_parse_judge_response_raises_on_missing_score_key():
    raw = '{"A": {"reasoning": "ok"}}'
    with pytest.raises(ValueError):
        parse_judge_response(raw, ["A"])


def test_parse_judge_response_raises_on_unparseable_text():
    with pytest.raises(ValueError):
        parse_judge_response("not json at all", ["A"])
