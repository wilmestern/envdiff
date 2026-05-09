"""Tests for env_differ_report and diff_report_cli."""

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import pytest

from envdiff.differ import DiffResult, DiffEntry, DiffStatus
from envdiff.env_differ_report import (
    DiffReport,
    build_diff_report,
    format_diff_report_text,
)
from envdiff.reporter import DiffSummary
from envdiff.env_stats import EnvStats


def _make_result(added=0, removed=0, changed=0):
    entries = []
    for i in range(added):
        entries.append(DiffEntry(key=f"ADD_{i}", status=DiffStatus.ADDED, left=None, right="v"))
    for i in range(removed):
        entries.append(DiffEntry(key=f"REM_{i}", status=DiffStatus.REMOVED, left="v", right=None))
    for i in range(changed):
        entries.append(DiffEntry(key=f"CHG_{i}", status=DiffStatus.CHANGED, left="a", right="b"))
    return DiffResult(entries=entries)


def _left_env():
    return {"DB_HOST": "localhost", "SECRET_KEY": "abc"}


def _right_env():
    return {"DB_HOST": "prod.host", "API_TOKEN": "tok"}


class TestBuildDiffReport:
    def test_returns_diff_report_instance(self):
        result = _make_result(added=1, removed=1)
        report = build_diff_report(result, _left_env(), _right_env(), "left", "right")
        assert isinstance(report, DiffReport)

    def test_names_are_stored(self):
        result = _make_result()
        report = build_diff_report(result, {}, {}, "staging", "production")
        assert report.left_name == "staging"
        assert report.right_name == "production"

    def test_title_stored(self):
        result = _make_result()
        report = build_diff_report(result, {}, {}, title="My Report")
        assert report.title == "My Report"

    def test_title_defaults_to_none(self):
        result = _make_result()
        report = build_diff_report(result, {}, {})
        assert report.title is None

    def test_has_differences_true_when_changes(self):
        result = _make_result(added=1)
        report = build_diff_report(result, {"A": "1"}, {})
        assert report.has_differences is True

    def test_has_differences_false_when_empty(self):
        result = _make_result()
        report = build_diff_report(result, {}, {})
        assert report.has_differences is False

    def test_as_dict_has_expected_keys(self):
        result = _make_result(added=1)
        report = build_diff_report(result, _left_env(), _right_env())
        d = report.as_dict()
        assert "summary" in d
        assert "left_stats" in d
        assert "right_stats" in d
        assert "has_differences" in d

    def test_summary_counts_match(self):
        result = _make_result(added=2, removed=1, changed=3)
        report = build_diff_report(result, _left_env(), _right_env())
        assert report.summary.added == 2
        assert report.summary.removed == 1
        assert report.summary.changed == 3


class TestFormatDiffReportText:
    def test_includes_names(self):
        result = _make_result()
        report = build_diff_report(result, {}, {}, "staging", "prod")
        text = format_diff_report_text(report)
        assert "staging" in text
        assert "prod" in text

    def test_includes_title_when_set(self):
        result = _make_result()
        report = build_diff_report(result, {}, {}, title="Weekly Check")
        text = format_diff_report_text(report)
        assert "Weekly Check" in text

    def test_no_differences_message(self):
        result = _make_result()
        report = build_diff_report(result, {}, {})
        text = format_diff_report_text(report)
        assert "No differences" in text

    def test_summary_line_present(self):
        result = _make_result(added=1, removed=2)
        report = build_diff_report(result, _left_env(), _right_env())
        text = format_diff_report_text(report)
        assert "+1 added" in text
        assert "-2 removed" in text


class TestDiffReportCli:
    def _run(self, left_data, right_data, extra_args=None):
        from envdiff.diff_report_cli import build_diff_report_parser, run_diff_report
        from envdiff.loader import EnvSource

        parser = build_diff_report_parser()
        args = parser.parse_args(["left.env", "right.env"] + (extra_args or []))
        out = StringIO()

        left_src = EnvSource(name="left.env", data=left_data)
        right_src = EnvSource(name="right.env", data=right_data)

        with patch("envdiff.diff_report_cli.load_from_file", side_effect=[left_src, right_src]):
            code = run_diff_report(args, out=out)

        return code, out.getvalue()

    def test_returns_zero_on_success(self):
        code, _ = self._run({"A": "1"}, {"A": "1"})
        assert code == 0

    def test_text_output_contains_names(self):
        _, output = self._run({"A": "1"}, {"B": "2"})
        assert "left.env" in output
        assert "right.env" in output

    def test_json_output_is_valid(self):
        _, output = self._run({"A": "1"}, {"A": "2"}, extra_args=["--format", "json"])
        data = json.loads(output)
        assert "summary" in data

    def test_title_appears_in_output(self):
        _, output = self._run({}, {}, extra_args=["--title", "CI Check"])
        assert "CI Check" in output

    def test_file_not_found_returns_one(self):
        from envdiff.diff_report_cli import build_diff_report_parser, run_diff_report
        parser = build_diff_report_parser()
        args = parser.parse_args(["missing.env", "also_missing.env"])
        with patch("envdiff.diff_report_cli.load_from_file", side_effect=FileNotFoundError("not found")):
            code = run_diff_report(args)
        assert code == 1
