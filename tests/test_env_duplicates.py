"""Tests for envdiff.env_duplicates."""

import pytest

from envdiff.env_duplicates import (
    DuplicateReport,
    detect_duplicates,
    find_case_aliases,
    find_exact_duplicates,
    format_duplicate_report_text,
)


# ---------------------------------------------------------------------------
# find_exact_duplicates
# ---------------------------------------------------------------------------

class TestFindExactDuplicates:
    def test_returns_empty_when_no_duplicates(self):
        result = find_exact_duplicates(["A", "B", "C"])
        assert result == {}

    def test_detects_single_duplicate(self):
        result = find_exact_duplicates(["A", "B", "A"])
        assert "A" in result
        assert result["A"] == [0, 2]

    def test_detects_multiple_duplicates(self):
        result = find_exact_duplicates(["X", "X", "Y", "Y"])
        assert set(result.keys()) == {"X", "Y"}

    def test_unique_keys_not_in_result(self):
        result = find_exact_duplicates(["A", "B", "A"])
        assert "B" not in result


# ---------------------------------------------------------------------------
# find_case_aliases
# ---------------------------------------------------------------------------

class TestFindCaseAliases:
    def test_no_aliases_when_all_unique(self):
        env = {"DATABASE_URL": "x", "SECRET_KEY": "y"}
        assert find_case_aliases(env) == []

    def test_detects_case_alias(self):
        env = {"Database_URL": "x", "DATABASE_URL": "y"}
        aliases = find_case_aliases(env)
        assert len(aliases) == 1
        pair = set(aliases[0])
        assert pair == {"Database_URL", "DATABASE_URL"}

    def test_same_key_twice_not_alias(self):
        # Exact duplicates are handled separately; same key same case = no alias
        env = {"KEY": "a"}  # dict can't hold two identical keys
        assert find_case_aliases(env) == []


# ---------------------------------------------------------------------------
# DuplicateReport
# ---------------------------------------------------------------------------

class TestDuplicateReport:
    def test_has_duplicates_false_when_empty(self):
        report = DuplicateReport(name="test")
        assert not report.has_duplicates

    def test_has_duplicates_true_with_exact(self):
        report = DuplicateReport(name="test", exact_duplicates={"KEY": [0, 2]})
        assert report.has_duplicates

    def test_has_duplicates_true_with_aliases(self):
        report = DuplicateReport(name="test", case_aliases=[("A", "a")])
        assert report.has_duplicates

    def test_as_dict_includes_all_fields(self):
        report = DuplicateReport(name="env", exact_duplicates={"K": [0, 1]}, case_aliases=[("A", "a")])
        d = report.as_dict()
        assert d["name"] == "env"
        assert "K" in d["exact_duplicates"]
        assert d["case_aliases"] == [{"a": "A", "b": "a"}]
        assert d["has_duplicates"] is True

    def test_repr_contains_name(self):
        report = DuplicateReport(name="staging")
        assert "staging" in repr(report)


# ---------------------------------------------------------------------------
# detect_duplicates
# ---------------------------------------------------------------------------

class TestDetectDuplicates:
    def test_clean_env_no_duplicates(self):
        env = {"A": "1", "B": "2", "C": "3"}
        report = detect_duplicates("clean", env)
        assert not report.has_duplicates

    def test_detects_case_alias_in_env(self):
        env = {"db_host": "localhost", "DB_HOST": "prod"}
        report = detect_duplicates("mixed", env)
        assert report.has_duplicates
        assert len(report.case_aliases) == 1


# ---------------------------------------------------------------------------
# format_duplicate_report_text
# ---------------------------------------------------------------------------

class TestFormatDuplicateReportText:
    def test_no_duplicates_message(self):
        report = DuplicateReport(name="prod")
        text = format_duplicate_report_text(report)
        assert "No duplicates" in text

    def test_includes_exact_duplicate_key(self):
        report = DuplicateReport(name="prod", exact_duplicates={"SECRET": [0, 3]})
        text = format_duplicate_report_text(report)
        assert "SECRET" in text

    def test_includes_alias_pair(self):
        report = DuplicateReport(name="prod", case_aliases=[("Key", "KEY")])
        text = format_duplicate_report_text(report)
        assert "Key" in text
        assert "KEY" in text
