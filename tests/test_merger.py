"""Tests for envdiff.merger module."""

import pytest

from envdiff.loader import EnvSource
from envdiff.merger import (
    MergeConflict,
    MergeStrategy,
    merge_envs,
)


def _src(name: str, data: dict) -> EnvSource:
    return EnvSource(name=name, data=data)


class TestMergeEnvs:
    def test_keys_only_in_left_are_included(self):
        left = _src("left", {"A": "1"})
        right = _src("right", {})
        result = merge_envs(left, right)
        assert result["A"] == "1"

    def test_keys_only_in_right_are_included(self):
        left = _src("left", {})
        right = _src("right", {"B": "2"})
        result = merge_envs(left, right)
        assert result["B"] == "2"

    def test_identical_keys_merged_once(self):
        left = _src("left", {"X": "same"})
        right = _src("right", {"X": "same"})
        result = merge_envs(left, right)
        assert result["X"] == "same"
        assert len(result) == 1

    def test_prefer_left_on_conflict(self):
        left = _src("left", {"K": "left_val"})
        right = _src("right", {"K": "right_val"})
        result = merge_envs(left, right, MergeStrategy.PREFER_LEFT)
        assert result["K"] == "left_val"

    def test_prefer_right_on_conflict(self):
        left = _src("left", {"K": "left_val"})
        right = _src("right", {"K": "right_val"})
        result = merge_envs(left, right, MergeStrategy.PREFER_RIGHT)
        assert result["K"] == "right_val"

    def test_raise_on_conflict_raises(self):
        left = _src("left", {"K": "v1"})
        right = _src("right", {"K": "v2"})
        with pytest.raises(MergeConflict) as exc_info:
            merge_envs(left, right, MergeStrategy.RAISE_ON_CONFLICT)
        assert exc_info.value.key == "K"
        assert exc_info.value.left_val == "v1"
        assert exc_info.value.right_val == "v2"

    def test_raise_on_conflict_does_not_raise_for_equal_values(self):
        left = _src("left", {"K": "same"})
        right = _src("right", {"K": "same"})
        result = merge_envs(left, right, MergeStrategy.RAISE_ON_CONFLICT)
        assert result["K"] == "same"

    def test_keep_both_creates_suffixed_keys(self):
        left = _src("staging", {"K": "v1"})
        right = _src("prod", {"K": "v2"})
        result = merge_envs(left, right, MergeStrategy.KEEP_BOTH)
        assert "K__STAGING" in result
        assert "K__PROD" in result
        assert result["K__STAGING"] == "v1"
        assert result["K__PROD"] == "v2"
        assert "K" not in result

    def test_keep_both_does_not_duplicate_equal_values(self):
        left = _src("staging", {"K": "same"})
        right = _src("prod", {"K": "same"})
        result = merge_envs(left, right, MergeStrategy.KEEP_BOTH)
        assert result["K"] == "same"

    def test_result_is_sorted(self):
        left = _src("l", {"Z": "1", "A": "2"})
        right = _src("r", {"M": "3"})
        result = merge_envs(left, right)
        assert list(result.keys()) == sorted(result.keys())

    def test_merge_conflict_str(self):
        exc = MergeConflict("KEY", "a", "b")
        assert "KEY" in str(exc)
        assert "a" in str(exc)
        assert "b" in str(exc)
