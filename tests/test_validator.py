"""Tests for envdiff.validator module."""

import pytest
from envdiff.validator import (
    ValidationIssue,
    ValidationResult,
    validate_required_keys,
    validate_no_empty_values,
    validate_env,
)


class TestValidationIssue:
    def test_defaults_to_error_severity(self):
        issue = ValidationIssue(key="FOO", message="missing")
        assert issue.severity == "error"

    def test_repr_contains_key_and_message(self):
        issue = ValidationIssue(key="BAR", message="empty value", severity="warning")
        r = repr(issue)
        assert "BAR" in r
        assert "warning" in r


class TestValidationResult:
    def test_is_valid_when_no_issues(self):
        result = ValidationResult()
        assert result.is_valid is True

    def test_is_invalid_when_error_present(self):
        result = ValidationResult(issues=[ValidationIssue(key="X", message="err", severity="error")])
        assert result.is_valid is False

    def test_is_valid_when_only_warnings(self):
        result = ValidationResult(issues=[ValidationIssue(key="X", message="warn", severity="warning")])
        assert result.is_valid is True

    def test_errors_filters_correctly(self):
        issues = [
            ValidationIssue(key="A", message="e", severity="error"),
            ValidationIssue(key="B", message="w", severity="warning"),
        ]
        result = ValidationResult(issues=issues)
        assert len(result.errors) == 1
        assert result.errors[0].key == "A"

    def test_warnings_filters_correctly(self):
        issues = [
            ValidationIssue(key="A", message="e", severity="error"),
            ValidationIssue(key="B", message="w", severity="warning"),
        ]
        result = ValidationResult(issues=issues)
        assert len(result.warnings) == 1
        assert result.warnings[0].key == "B"


class TestValidateRequiredKeys:
    def test_no_issues_when_all_present(self):
        issues = validate_required_keys({"A": "1", "B": "2"}, ["A", "B"])
        assert issues == []

    def test_reports_missing_key(self):
        issues = validate_required_keys({"A": "1"}, ["A", "B"])
        assert len(issues) == 1
        assert issues[0].key == "B"
        assert issues[0].severity == "error"

    def test_empty_required_list_yields_no_issues(self):
        issues = validate_required_keys({"A": "1"}, [])
        assert issues == []


class TestValidateNoEmptyValues:
    def test_no_issues_when_all_filled(self):
        issues = validate_no_empty_values({"A": "1", "B": "2"})
        assert issues == []

    def test_reports_empty_as_error_by_default(self):
        issues = validate_no_empty_values({"A": ""})
        assert len(issues) == 1
        assert issues[0].severity == "error"

    def test_reports_empty_as_warning_when_flagged(self):
        issues = validate_no_empty_values({"A": ""}, warn_only=True)
        assert issues[0].severity == "warning"


class TestValidateEnv:
    def test_valid_env_returns_valid_result(self):
        env = {"HOST": "localhost", "PORT": "8080"}
        result = validate_env(env, required_keys=["HOST", "PORT"])
        assert result.is_valid
        assert result.issues == []

    def test_missing_required_key_makes_invalid(self):
        result = validate_env({}, required_keys=["DB_URL"])
        assert not result.is_valid
        assert result.errors[0].key == "DB_URL"

    def test_empty_value_warn_produces_warning(self):
        result = validate_env({"X": ""}, warn_empty=True)
        assert result.is_valid
        assert len(result.warnings) == 1

    def test_empty_value_error_produces_error(self):
        result = validate_env({"X": ""}, error_empty=True)
        assert not result.is_valid
        assert len(result.errors) == 1

    def test_combined_required_and_empty_check(self):
        env = {"A": "", "B": "ok"}
        result = validate_env(env, required_keys=["A", "B", "C"], error_empty=True)
        keys = {i.key for i in result.errors}
        assert "A" in keys  # empty value
        assert "C" in keys  # missing required
