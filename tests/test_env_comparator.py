"""Tests for envdiff.env_comparator."""

import pytest

from envdiff.env_comparator import (
    ComparatorRow,
    ComparisonResult,
    compare_envs,
    format_comparison_text,
)


def _row(key, lv, rv, status="unchanged", sensitive=False):
    return ComparatorRow(
        key=key,
        left_value=lv,
        right_value=rv,
        status=status,
        is_sensitive=sensitive,
    )


class TestComparatorRow:
    def test_as_dict_has_expected_keys(self):
        row = _row("APP_ENV", "staging", "production", "changed")
        d = row.as_dict()
        assert set(d) == {"key", "left", "right", "sensitive", "status"}

    def test_repr_contains_key_and_status(self):
        row = _row("APP_ENV", "staging", "production", "changed")
        assert "APP_ENV" in repr(row)
        assert "changed" in repr(row)

    def test_sensitive_flag_in_dict(self):
        row = _row("SECRET_KEY", "x", "y", "changed", sensitive=True)
        assert row.as_dict()["sensitive"] is True


class TestComparisonResult:
    def test_has_differences_false_when_all_unchanged(self):
        result = ComparisonResult(
            left_name="a",
            right_name="b",
            rows=[_row("K", "v", "v", "unchanged")],
        )
        assert result.has_differences is False

    def test_has_differences_true_when_changed(self):
        result = ComparisonResult(
            left_name="a",
            right_name="b",
            rows=[_row("K", "v1", "v2", "changed")],
        )
        assert result.has_differences is True

    def test_changed_rows_filters_correctly(self):
        rows = [
            _row("A", "x", "x", "unchanged"),
            _row("B", None, "y", "added"),
            _row("C", "z", None, "removed"),
        ]
        result = ComparisonResult(left_name="l", right_name="r", rows=rows)
        changed = result.changed_rows()
        assert len(changed) == 2
        assert all(r.key in ("B", "C") for r in changed)

    def test_as_dict_structure(self):
        result = ComparisonResult(left_name="l", right_name="r", rows=[])
        d = result.as_dict()
        assert d["left"] == "l"
        assert d["right"] == "r"
        assert d["rows"] == []


class TestCompareEnvs:
    def test_detects_added_key(self):
        result = compare_envs({}, {"NEW_KEY": "val"})
        assert any(r.key == "NEW_KEY" and r.status == "added" for r in result.rows)

    def test_detects_removed_key(self):
        result = compare_envs({"OLD_KEY": "val"}, {})
        assert any(r.key == "OLD_KEY" and r.status == "removed" for r in result.rows)

    def test_detects_changed_key(self):
        result = compare_envs({"K": "a"}, {"K": "b"})
        assert any(r.key == "K" and r.status == "changed" for r in result.rows)

    def test_unchanged_key_status(self):
        result = compare_envs({"K": "v"}, {"K": "v"}, include_unchanged=True)
        assert any(r.key == "K" and r.status == "unchanged" for r in result.rows)

    def test_exclude_unchanged_by_default(self):
        result = compare_envs({"K": "v"}, {"K": "v"}, include_unchanged=False)
        assert not any(r.key == "K" for r in result.rows)

    def test_redacts_sensitive_values(self):
        result = compare_envs(
            {"DB_PASSWORD": "secret1"},
            {"DB_PASSWORD": "secret2"},
            redact=True,
        )
        row = next(r for r in result.rows if r.key == "DB_PASSWORD")
        assert row.left_value != "secret1"
        assert row.right_value != "secret2"
        assert row.is_sensitive is True

    def test_no_redact_shows_plain_values(self):
        result = compare_envs(
            {"DB_PASSWORD": "plain"},
            {"DB_PASSWORD": "plain"},
            redact=False,
            include_unchanged=True,
        )
        row = next(r for r in result.rows if r.key == "DB_PASSWORD")
        assert row.left_value == "plain"

    def test_keys_sorted_alphabetically(self):
        result = compare_envs(
            {"Z": "1", "A": "2"},
            {"Z": "1", "A": "2"},
            include_unchanged=True,
        )
        keys = [r.key for r in result.rows]
        assert keys == sorted(keys)

    def test_names_propagated(self):
        result = compare_envs({}, {}, left_name="staging", right_name="prod")
        assert result.left_name == "staging"
        assert result.right_name == "prod"


class TestFormatComparisonText:
    def test_returns_string(self):
        result = compare_envs({"A": "1"}, {"A": "2"})
        text = format_comparison_text(result)
        assert isinstance(text, str)

    def test_contains_key(self):
        result = compare_envs({"MY_KEY": "old"}, {"MY_KEY": "new"})
        text = format_comparison_text(result)
        assert "MY_KEY" in text

    def test_contains_column_headers(self):
        result = compare_envs({}, {}, left_name="staging", right_name="prod")
        text = format_comparison_text(result)
        assert "staging" in text
        assert "prod" in text
