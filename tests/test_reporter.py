"""Tests for envdiff.reporter module."""
import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.reporter import DiffSummary, format_summary_text, summarize


def _make_result(*entries):
    return DiffResult(entries=list(entries))


def _entry(key, status, old=None, new=None):
    return DiffEntry(key=key, status=status, old_value=old, new_value=new)


class TestSummarize:
    def test_empty_result(self):
        result = _make_result()
        s = summarize(result)
        assert s.total == 0
        assert s.added == 0
        assert s.removed == 0
        assert s.changed == 0
        assert s.unchanged == 0
        assert s.redacted == 0

    def test_counts_added(self):
        result = _make_result(_entry("A", DiffStatus.ADDED, new="1"))
        s = summarize(result)
        assert s.added == 1
        assert s.total == 1

    def test_counts_removed(self):
        result = _make_result(_entry("A", DiffStatus.REMOVED, old="1"))
        s = summarize(result)
        assert s.removed == 1

    def test_counts_changed(self):
        result = _make_result(_entry("A", DiffStatus.CHANGED, old="1", new="2"))
        s = summarize(result)
        assert s.changed == 1

    def test_counts_unchanged(self):
        result = _make_result(_entry("A", DiffStatus.UNCHANGED, old="1", new="1"))
        s = summarize(result)
        assert s.unchanged == 1

    def test_counts_redacted_old_value(self):
        result = _make_result(
            _entry("SECRET", DiffStatus.CHANGED, old="[REDACTED]", new="[REDACTED]")
        )
        s = summarize(result)
        assert s.redacted == 1

    def test_mixed_entries(self):
        result = _make_result(
            _entry("A", DiffStatus.ADDED, new="x"),
            _entry("B", DiffStatus.REMOVED, old="y"),
            _entry("C", DiffStatus.CHANGED, old="1", new="2"),
            _entry("D", DiffStatus.UNCHANGED, old="z", new="z"),
        )
        s = summarize(result)
        assert s.total == 4
        assert s.added == 1
        assert s.removed == 1
        assert s.changed == 1
        assert s.unchanged == 1


class TestHasDifferences:
    def test_true_when_changes_exist(self):
        s = DiffSummary(total=2, added=1, removed=0, changed=1, unchanged=0, redacted=0)
        assert s.has_differences() is True

    def test_false_when_only_unchanged(self):
        s = DiffSummary(total=3, added=0, removed=0, changed=0, unchanged=3, redacted=0)
        assert s.has_differences() is False


class TestFormatSummaryText:
    def test_contains_section_header(self):
        s = DiffSummary(total=1, added=1, removed=0, changed=0, unchanged=0, redacted=0)
        text = format_summary_text(s)
        assert "Summary" in text

    def test_shows_counts(self):
        s = DiffSummary(total=5, added=2, removed=1, changed=1, unchanged=1, redacted=0)
        text = format_summary_text(s)
        assert "Added:     2" in text
        assert "Removed:   1" in text
        assert "Changed:   1" in text
        assert "Total:     5" in text

    def test_no_differences_message(self):
        s = DiffSummary(total=2, added=0, removed=0, changed=0, unchanged=2, redacted=0)
        text = format_summary_text(s)
        assert "no differences" in text

    def test_as_dict_keys(self):
        s = DiffSummary(total=0, added=0, removed=0, changed=0, unchanged=0, redacted=0)
        d = s.as_dict()
        assert set(d.keys()) == {"total", "added", "removed", "changed", "unchanged", "redacted"}
