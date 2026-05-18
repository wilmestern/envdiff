"""Tests for envdiff.env_deduplicator."""

import pytest

from envdiff.env_deduplicator import (
    DeduplicationResult,
    deduplicate_env,
    format_deduplication_text,
)


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# DeduplicationResult
# ---------------------------------------------------------------------------

class TestDeduplicationResult:
    def test_removed_count_matches_list(self):
        r = DeduplicationResult(
            original_count=4,
            deduplicated={"A": "1"},
            removed_keys=["B", "C"],
        )
        assert r.removed_count == 2

    def test_has_duplicates_true(self):
        r = DeduplicationResult(original_count=2, removed_keys=["B"])
        assert r.has_duplicates is True

    def test_has_duplicates_false_when_empty(self):
        r = DeduplicationResult(original_count=1)
        assert r.has_duplicates is False

    def test_as_dict_keys(self):
        r = DeduplicationResult(original_count=3, removed_keys=["X"])
        d = r.as_dict()
        assert "original_count" in d
        assert "deduplicated_count" in d
        assert "removed_count" in d
        assert "removed_keys" in d
        assert "value_groups" in d

    def test_repr_contains_counts(self):
        r = DeduplicationResult(original_count=5, removed_keys=["A", "B"])
        text = repr(r)
        assert "5" in text
        assert "2" in text


# ---------------------------------------------------------------------------
# deduplicate_env
# ---------------------------------------------------------------------------

class TestDeduplicateEnv:
    def test_empty_env_returns_empty(self):
        result = deduplicate_env({})
        assert result.deduplicated == {}
        assert result.removed_keys == []

    def test_no_duplicates_unchanged(self):
        env = _env(A="1", B="2", C="3")
        result = deduplicate_env(env)
        assert result.deduplicated == env
        assert result.removed_count == 0

    def test_detects_duplicate_values(self):
        env = _env(A="same", B="same", C="other")
        result = deduplicate_env(env)
        assert result.has_duplicates is True
        assert result.removed_count == 1

    def test_keeps_first_by_default(self):
        env = _env(B="dup", A="dup")
        result = deduplicate_env(env, keep="first")
        assert "A" in result.deduplicated
        assert "B" not in result.deduplicated
        assert "B" in result.removed_keys

    def test_keeps_last_when_specified(self):
        env = _env(A="dup", B="dup")
        result = deduplicate_env(env, keep="last")
        assert "B" in result.deduplicated
        assert "A" in result.removed_keys

    def test_original_count_is_correct(self):
        env = _env(A="v", B="v", C="other")
        result = deduplicate_env(env)
        assert result.original_count == 3

    def test_value_groups_populated(self):
        env = _env(X="shared", Y="shared", Z="unique")
        result = deduplicate_env(env)
        assert "shared" in result.value_groups
        assert set(result.value_groups["shared"]) == {"X", "Y"}

    def test_as_dict_value_groups_only_shows_duplicates(self):
        env = _env(A="dup", B="dup", C="solo")
        result = deduplicate_env(env)
        d = result.as_dict()
        assert "dup" in d["value_groups"]
        assert "solo" not in d["value_groups"]


# ---------------------------------------------------------------------------
# format_deduplication_text
# ---------------------------------------------------------------------------

class TestFormatDeduplicationText:
    def test_contains_original_count(self):
        env = _env(A="1", B="2")
        result = deduplicate_env(env)
        text = format_deduplication_text(result)
        assert "2" in text

    def test_shows_duplicate_group(self):
        env = _env(A="same", B="same")
        result = deduplicate_env(env)
        text = format_deduplication_text(result)
        assert "same" in text

    def test_no_group_section_when_no_duplicates(self):
        env = _env(A="1", B="2")
        result = deduplicate_env(env)
        text = format_deduplication_text(result)
        assert "Duplicate groups" not in text

    def test_long_value_is_truncated(self):
        long_val = "x" * 80
        env = {"KEY1": long_val, "KEY2": long_val}
        result = deduplicate_env(env)
        text = format_deduplication_text(result)
        assert "..." in text
