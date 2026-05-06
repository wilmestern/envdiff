"""Tests for envdiff.env_normalizer."""

import pytest
from envdiff.env_normalizer import (
    normalize_key,
    normalize_value,
    normalize_env,
    find_duplicate_keys,
)


class TestNormalizeKey:
    def test_uppercases_by_default(self):
        assert normalize_key("db_host") == "DB_HOST"

    def test_strips_whitespace_by_default(self):
        assert normalize_key("  MY_KEY  ") == "MY_KEY"

    def test_no_uppercase_when_disabled(self):
        assert normalize_key("db_host", uppercase=False) == "db_host"

    def test_no_strip_when_disabled(self):
        assert normalize_key("  key  ", strip=False) == "  KEY  "

    def test_already_normalized_unchanged(self):
        assert normalize_key("APP_PORT") == "APP_PORT"


class TestNormalizeValue:
    def test_strips_whitespace_by_default(self):
        assert normalize_value("  hello  ") == "hello"

    def test_no_strip_when_disabled(self):
        assert normalize_value("  hello  ", strip=False) == "  hello  "

    def test_collapse_whitespace(self):
        assert normalize_value("foo   bar\tbaz", collapse_whitespace=True) == "foo bar baz"

    def test_collapse_whitespace_with_strip(self):
        assert normalize_value("  foo   bar  ", collapse_whitespace=True) == "foo bar"

    def test_empty_value_unchanged(self):
        assert normalize_value("") == ""


class TestNormalizeEnv:
    def test_uppercases_all_keys(self):
        result = normalize_env({"db_host": "localhost", "app_port": "8080"})
        assert "DB_HOST" in result
        assert "APP_PORT" in result

    def test_strips_values(self):
        result = normalize_env({"KEY": "  value  "})
        assert result["KEY"] == "value"

    def test_drop_empty_values(self):
        result = normalize_env({"KEY": "", "OTHER": "val"}, drop_empty_values=True)
        assert "KEY" not in result
        assert result["OTHER"] == "val"

    def test_keeps_empty_values_by_default(self):
        result = normalize_env({"KEY": ""})
        assert "KEY" in result
        assert result["KEY"] == ""

    def test_collapse_whitespace_in_values(self):
        result = normalize_env({"MSG": "hello   world"}, collapse_whitespace=True)
        assert result["MSG"] == "hello world"

    def test_returns_new_dict(self):
        original = {"KEY": "val"}
        result = normalize_env(original)
        assert result is not original

    def test_empty_env_returns_empty(self):
        assert normalize_env({}) == {}


class TestFindDuplicateKeys:
    def test_no_duplicates_returns_empty(self):
        env = {"DB_HOST": "a", "APP_PORT": "b"}
        assert find_duplicate_keys(env) == {}

    def test_detects_case_collision(self):
        env = {"db_host": "a", "DB_HOST": "b"}
        duplicates = find_duplicate_keys(env)
        assert "DB_HOST" in duplicates

    def test_returns_later_key_as_duplicate(self):
        # dict preserves insertion order; second occurrence is the duplicate
        env = {"api_key": "x", "API_KEY": "y"}
        duplicates = find_duplicate_keys(env)
        assert duplicates.get("API_KEY") == "API_KEY"

    def test_empty_env_returns_empty(self):
        assert find_duplicate_keys({}) == {}
