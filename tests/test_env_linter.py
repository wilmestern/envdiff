"""Tests for envdiff.env_linter."""

import pytest
from envdiff.env_linter import LintIssue, LintResult, lint_env, format_lint_text


class TestLintIssue:
    def test_defaults_to_warning(self):
        issue = LintIssue("KEY", "some message")
        assert issue.severity == "warning"

    def test_repr_contains_key_and_message(self):
        issue = LintIssue("KEY", "bad value", "error")
        assert "KEY" in repr(issue)
        assert "bad value" in repr(issue)

    def test_as_dict_has_expected_keys(self):
        issue = LintIssue("FOO", "msg", "warning")
        d = issue.as_dict()
        assert d["key"] == "FOO"
        assert d["message"] == "msg"
        assert d["severity"] == "warning"


class TestLintResult:
    def test_has_issues_false_when_empty(self):
        result = LintResult()
        assert not result.has_issues

    def test_has_issues_true_when_populated(self):
        result = LintResult(issues=[LintIssue("K", "m")])
        assert result.has_issues

    def test_errors_filters_by_severity(self):
        result = LintResult(issues=[
            LintIssue("A", "err", "error"),
            LintIssue("B", "warn", "warning"),
        ])
        assert len(result.errors) == 1
        assert result.errors[0].key == "A"

    def test_warnings_filters_by_severity(self):
        result = LintResult(issues=[
            LintIssue("A", "err", "error"),
            LintIssue("B", "warn", "warning"),
        ])
        assert len(result.warnings) == 1

    def test_as_dict_includes_counts(self):
        result = LintResult(issues=[
            LintIssue("A", "e", "error"),
            LintIssue("B", "w", "warning"),
        ])
        d = result.as_dict()
        assert d["issue_count"] == 2
        assert d["error_count"] == 1
        assert d["warning_count"] == 1


class TestLintEnv:
    def test_clean_env_has_no_issues(self):
        result = lint_env({"DATABASE_URL": "postgres://localhost/db", "PORT": "8080"})
        assert not result.has_issues

    def test_lowercase_key_triggers_warning(self):
        result = lint_env({"database_url": "value"})
        keys = [i.key for i in result.warnings]
        assert "database_url" in keys

    def test_key_with_space_triggers_error(self):
        result = lint_env({"BAD KEY": "value"})
        assert any(i.severity == "error" and "BAD KEY" == i.key for i in result.issues)

    def test_sensitive_empty_value_triggers_error(self):
        result = lint_env({"DB_PASSWORD": ""})
        assert any(i.severity == "error" for i in result.issues)

    def test_unresolved_placeholder_triggers_warning(self):
        result = lint_env({"API_URL": "${BASE_URL}"})
        assert any("unresolved" in i.message.lower() for i in result.warnings)

    def test_single_char_value_triggers_warning(self):
        result = lint_env({"MODE": "x"})
        assert any("short" in i.message.lower() for i in result.warnings)


class TestFormatLintText:
    def test_no_issues_message(self):
        result = LintResult()
        text = format_lint_text(result)
        assert "No issues found" in text

    def test_includes_name_in_header(self):
        result = LintResult()
        text = format_lint_text(result, name="staging.env")
        assert "staging.env" in text

    def test_lists_issues(self):
        result = LintResult(issues=[LintIssue("KEY", "some problem", "warning")])
        text = format_lint_text(result)
        assert "KEY" in text
        assert "some problem" in text
