"""Tests for envdiff.lint_cli."""

import json
import pytest
from unittest.mock import patch, MagicMock
from envdiff.lint_cli import build_lint_parser, run_lint
from envdiff.env_linter import LintResult, LintIssue


class TestBuildLintParser:
    def test_requires_at_least_one_file(self):
        parser = build_lint_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_single_file(self):
        parser = build_lint_parser()
        args = parser.parse_args(["staging.env"])
        assert args.files == ["staging.env"]

    def test_parses_multiple_files(self):
        parser = build_lint_parser()
        args = parser.parse_args(["a.env", "b.env"])
        assert args.files == ["a.env", "b.env"]

    def test_default_format_is_text(self):
        parser = build_lint_parser()
        args = parser.parse_args(["f.env"])
        assert args.format == "text"

    def test_json_format(self):
        parser = build_lint_parser()
        args = parser.parse_args(["f.env", "--format", "json"])
        assert args.format == "json"

    def test_strict_defaults_false(self):
        parser = build_lint_parser()
        args = parser.parse_args(["f.env"])
        assert args.strict is False

    def test_strict_flag(self):
        parser = build_lint_parser()
        args = parser.parse_args(["f.env", "--strict"])
        assert args.strict is True


class TestRunLint:
    def _make_args(self, files, fmt="text", strict=False):
        args = MagicMock()
        args.files = files
        args.format = fmt
        args.strict = strict
        return args

    def _mock_lint_file(self, result):
        return patch("envdiff.lint_cli._lint_file", return_value=("test.env", result))

    def test_returns_zero_on_clean(self, capsys):
        clean = LintResult()
        args = self._make_args(["test.env"])
        with self._mock_lint_file(clean):
            code = run_lint(args)
        assert code == 0

    def test_returns_two_on_errors(self, capsys):
        result = LintResult(issues=[LintIssue("K", "bad", "error")])
        args = self._make_args(["test.env"])
        with self._mock_lint_file(result):
            code = run_lint(args)
        assert code == 2

    def test_returns_one_on_warnings_with_strict(self, capsys):
        result = LintResult(issues=[LintIssue("K", "warn", "warning")])
        args = self._make_args(["test.env"], strict=True)
        with self._mock_lint_file(result):
            code = run_lint(args)
        assert code == 1

    def test_returns_zero_on_warnings_without_strict(self, capsys):
        result = LintResult(issues=[LintIssue("K", "warn", "warning")])
        args = self._make_args(["test.env"], strict=False)
        with self._mock_lint_file(result):
            code = run_lint(args)
        assert code == 0

    def test_json_output_is_valid(self, capsys):
        clean = LintResult()
        args = self._make_args(["test.env"], fmt="json")
        with self._mock_lint_file(clean):
            run_lint(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "test.env" in data
