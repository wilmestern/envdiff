"""Tests for envdiff.env_filter."""

import pytest

from envdiff.env_filter import (
    exclude_keys,
    filter_by_pattern,
    filter_by_prefix,
    select_keys,
)

SAMPLE: dict = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "APP_SECRET": "abc",
    "APP_DEBUG": "true",
    "LOG_LEVEL": "info",
}


class TestFilterByPrefix:
    def test_returns_matching_keys(self):
        result = filter_by_prefix(SAMPLE, ["DB_"])
        assert set(result.keys()) == {"DB_HOST", "DB_PORT"}

    def test_multiple_prefixes(self):
        result = filter_by_prefix(SAMPLE, ["DB_", "APP_"])
        assert set(result.keys()) == {"DB_HOST", "DB_PORT", "APP_SECRET", "APP_DEBUG"}

    def test_empty_prefixes_returns_all(self):
        result = filter_by_prefix(SAMPLE, [])
        assert result == SAMPLE

    def test_case_insensitive_by_default(self):
        result = filter_by_prefix(SAMPLE, ["db_"])
        assert set(result.keys()) == {"DB_HOST", "DB_PORT"}

    def test_case_sensitive_mode(self):
        result = filter_by_prefix(SAMPLE, ["db_"], case_sensitive=True)
        assert result == {}

    def test_no_match_returns_empty(self):
        result = filter_by_prefix(SAMPLE, ["REDIS_"])
        assert result == {}


class TestFilterByPattern:
    def test_glob_star(self):
        result = filter_by_pattern(SAMPLE, ["DB_*"])
        assert set(result.keys()) == {"DB_HOST", "DB_PORT"}

    def test_question_mark_wildcard(self):
        result = filter_by_pattern(SAMPLE, ["DB_HOS?"])
        assert set(result.keys()) == {"DB_HOST"}

    def test_multiple_patterns(self):
        result = filter_by_pattern(SAMPLE, ["DB_*", "LOG_*"])
        assert set(result.keys()) == {"DB_HOST", "DB_PORT", "LOG_LEVEL"}

    def test_empty_patterns_returns_all(self):
        result = filter_by_pattern(SAMPLE, [])
        assert result == SAMPLE

    def test_case_insensitive_by_default(self):
        result = filter_by_pattern(SAMPLE, ["app_*"])
        assert set(result.keys()) == {"APP_SECRET", "APP_DEBUG"}

    def test_case_sensitive_mode(self):
        result = filter_by_pattern(SAMPLE, ["app_*"], case_sensitive=True)
        assert result == {}


class TestExcludeKeys:
    def test_removes_specified_key(self):
        result = exclude_keys(SAMPLE, ["DB_HOST"])
        assert "DB_HOST" not in result
        assert "DB_PORT" in result

    def test_case_insensitive_by_default(self):
        result = exclude_keys(SAMPLE, ["db_host"])
        assert "DB_HOST" not in result

    def test_case_sensitive_keeps_key(self):
        result = exclude_keys(SAMPLE, ["db_host"], case_sensitive=True)
        assert "DB_HOST" in result

    def test_missing_key_ignored(self):
        result = exclude_keys(SAMPLE, ["NONEXISTENT"])
        assert result == SAMPLE


class TestSelectKeys:
    def test_returns_only_specified_keys(self):
        result = select_keys(SAMPLE, ["DB_HOST", "LOG_LEVEL"])
        assert set(result.keys()) == {"DB_HOST", "LOG_LEVEL"}

    def test_missing_keys_skipped(self):
        result = select_keys(SAMPLE, ["DB_HOST", "MISSING"])
        assert set(result.keys()) == {"DB_HOST"}

    def test_case_insensitive_by_default(self):
        result = select_keys(SAMPLE, ["db_host"])
        assert "DB_HOST" in result

    def test_case_sensitive_mode(self):
        result = select_keys(SAMPLE, ["db_host"], case_sensitive=True)
        assert result == {}
