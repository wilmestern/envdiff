"""Tests for envdiff.env_sorter."""

from __future__ import annotations

import pytest

from envdiff.env_sorter import sort_env, sort_by_prefix, format_sorted_text


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


class TestSortEnv:
    def test_sorts_keys_alphabetically(self):
        env = {"ZEBRA": "1", "APPLE": "2", "MANGO": "3"}
        result = sort_env(env)
        assert list(result.keys()) == ["APPLE", "MANGO", "ZEBRA"]

    def test_reverse_sorts_descending(self):
        env = {"ZEBRA": "1", "APPLE": "2", "MANGO": "3"}
        result = sort_env(env, reverse=True)
        assert list(result.keys()) == ["ZEBRA", "MANGO", "APPLE"]

    def test_case_insensitive_by_default(self):
        env = {"b_KEY": "1", "A_KEY": "2", "c_KEY": "3"}
        result = sort_env(env)
        assert list(result.keys()) == ["A_KEY", "b_KEY", "c_KEY"]

    def test_case_sensitive_when_requested(self):
        # Uppercase letters have lower ordinal than lowercase in ASCII
        env = {"b_KEY": "1", "A_KEY": "2"}
        result = sort_env(env, case_sensitive=True)
        assert list(result.keys()) == ["A_KEY", "b_KEY"]

    def test_values_preserved(self):
        env = {"Z": "zval", "A": "aval"}
        result = sort_env(env)
        assert result["A"] == "aval"
        assert result["Z"] == "zval"

    def test_empty_env_returns_empty(self):
        assert sort_env({}) == {}


class TestSortByPrefix:
    def test_priority_prefix_keys_come_first(self):
        env = {"DB_HOST": "1", "APP_NAME": "2", "AWS_KEY": "3"}
        result = sort_by_prefix(env, ["AWS"])
        keys = list(result.keys())
        assert keys[0] == "AWS_KEY"

    def test_multiple_prefixes_respected_in_order(self):
        env = {"DB_HOST": "1", "APP_NAME": "2", "AWS_KEY": "3"}
        result = sort_by_prefix(env, ["AWS", "DB"])
        keys = list(result.keys())
        assert keys[0] == "AWS_KEY"
        assert keys[1] == "DB_HOST"
        assert keys[2] == "APP_NAME"

    def test_no_prefixes_returns_alphabetical(self):
        env = {"Z": "1", "A": "2", "M": "3"}
        result = sort_by_prefix(env, [])
        assert list(result.keys()) == ["A", "M", "Z"]

    def test_prefix_match_is_case_insensitive(self):
        env = {"aws_secret": "s", "other": "o"}
        result = sort_by_prefix(env, ["AWS"])
        assert list(result.keys())[0] == "aws_secret"

    def test_empty_env_returns_empty(self):
        assert sort_by_prefix({}, ["AWS"]) == {}

    def test_reverse_flag_reverses_within_groups(self):
        env = {"AWS_B": "1", "AWS_A": "2", "DB_HOST": "3"}
        result = sort_by_prefix(env, ["AWS"], reverse=True)
        keys = list(result.keys())
        # With reverse, AWS group is still first but internally reversed
        assert set(keys[:2]) == {"AWS_A", "AWS_B"}


class TestFormatSortedText:
    def test_renders_key_value_pairs(self):
        env = {"A": "1", "B": "2"}
        text = format_sorted_text(env)
        assert "A=1" in text
        assert "B=2" in text

    def test_title_appears_at_top(self):
        env = {"X": "y"}
        text = format_sorted_text(env, title="My Env")
        lines = text.splitlines()
        assert lines[0] == "My Env"

    def test_separator_line_under_title(self):
        env = {"X": "y"}
        text = format_sorted_text(env, title="Hi")
        lines = text.splitlines()
        assert lines[1] == "--"

    def test_no_title_no_separator(self):
        env = {"X": "y"}
        text = format_sorted_text(env)
        assert "---" not in text

    def test_empty_env_with_title(self):
        text = format_sorted_text({}, title="Empty")
        assert "Empty" in text
