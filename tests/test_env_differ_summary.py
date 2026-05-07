"""Tests for envdiff.env_differ_summary."""

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.env_differ_summary import (
    GroupedDiffSummary,
    _extract_prefix,
    format_grouped_summary_text,
    grouped_diff_summary,
)


def _entry(key: str, status: DiffStatus, left=None, right=None) -> DiffEntry:
    return DiffEntry(key=key, status=status, left_value=left, right_value=right)


def _result(*entries: DiffEntry) -> DiffResult:
    return DiffResult(entries=list(entries))


# ---------------------------------------------------------------------------
# _extract_prefix
# ---------------------------------------------------------------------------

class TestExtractPrefix:
    def test_returns_first_segment(self):
        assert _extract_prefix("DB_HOST") == "DB"

    def test_no_sep_returns_other(self):
        assert _extract_prefix("NOPREFIX") == "__other__"

    def test_custom_sep(self):
        assert _extract_prefix("APP.SECRET", sep=".") == "APP"

    def test_multiple_underscores_uses_first(self):
        assert _extract_prefix("AWS_S3_BUCKET") == "AWS"


# ---------------------------------------------------------------------------
# grouped_diff_summary
# ---------------------------------------------------------------------------

class TestGroupedDiffSummary:
    def _build(self):
        entries = [
            _entry("DB_HOST", DiffStatus.CHANGED, "old", "new"),
            _entry("DB_PORT", DiffStatus.UNCHANGED, "5432", "5432"),
            _entry("APP_KEY", DiffStatus.ADDED, None, "xyz"),
            _entry("LEGACY", DiffStatus.REMOVED, "old", None),
        ]
        return grouped_diff_summary(_result(*entries), name_left="staging", name_right="prod")

    def test_names_stored(self):
        s = self._build()
        assert s.name_left == "staging"
        assert s.name_right == "prod"

    def test_totals_correct(self):
        s = self._build()
        assert s.total_added == 1
        assert s.total_removed == 1
        assert s.total_changed == 1
        assert s.total_unchanged == 1

    def test_has_differences_true(self):
        s = self._build()
        assert s.has_differences is True

    def test_has_differences_false_when_only_unchanged(self):
        entries = [_entry("A_KEY", DiffStatus.UNCHANGED, "v", "v")]
        s = grouped_diff_summary(_result(*entries))
        assert s.has_differences is False

    def test_by_prefix_keys(self):
        s = self._build()
        assert "DB" in s.by_prefix
        assert "APP" in s.by_prefix
        assert "__other__" in s.by_prefix

    def test_db_prefix_counts(self):
        s = self._build()
        db = s.by_prefix["DB"]
        assert db.changed == 1
        assert db.unchanged == 1
        assert db.added == 0

    def test_as_dict_has_expected_keys(self):
        s = self._build()
        d = s.as_dict()
        for key in ("name_left", "name_right", "total_added", "total_removed",
                    "total_changed", "total_unchanged", "has_differences", "by_prefix"):
            assert key in d

    def test_empty_result(self):
        s = grouped_diff_summary(_result())
        assert s.total_added == 0
        assert s.by_prefix == {}


# ---------------------------------------------------------------------------
# format_grouped_summary_text
# ---------------------------------------------------------------------------

class TestFormatGroupedSummaryText:
    def test_contains_names(self):
        s = grouped_diff_summary(_result(), name_left="A", name_right="B")
        text = format_grouped_summary_text(s)
        assert "'A'" in text
        assert "'B'" in text

    def test_contains_totals(self):
        entries = [_entry("X_KEY", DiffStatus.ADDED, None, "v")]
        s = grouped_diff_summary(_result(*entries))
        text = format_grouped_summary_text(s)
        assert "Added:" in text
        assert "1" in text

    def test_contains_prefix_section(self):
        entries = [_entry("DB_HOST", DiffStatus.CHANGED, "a", "b")]
        s = grouped_diff_summary(_result(*entries))
        text = format_grouped_summary_text(s)
        assert "By prefix" in text
        assert "DB" in text
