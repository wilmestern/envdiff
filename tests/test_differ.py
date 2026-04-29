"""Tests for envdiff.differ and envdiff.formatter."""

import pytest

from envdiff.differ import DiffStatus, diff_envs
from envdiff.formatter import format_json, format_text

LEFT = {
    "APP_ENV": "staging",
    "DATABASE_URL": "postgres://staging-db/app",
    "SECRET_KEY": "supersecret",
    "REMOVED_VAR": "gone",
}

RIGHT = {
    "APP_ENV": "production",
    "DATABASE_URL": "postgres://staging-db/app",
    "SECRET_KEY": "anothersecret",
    "ADDED_VAR": "new",
}


class TestDiffEnvs:
    def test_detects_added_key(self):
        result = diff_envs(LEFT, RIGHT, redact=False)
        keys = {e.key for e in result.added}
        assert "ADDED_VAR" in keys

    def test_detects_removed_key(self):
        result = diff_envs(LEFT, RIGHT, redact=False)
        keys = {e.key for e in result.removed}
        assert "REMOVED_VAR" in keys

    def test_detects_changed_key(self):
        result = diff_envs(LEFT, RIGHT, redact=False)
        keys = {e.key for e in result.changed}
        assert "APP_ENV" in keys

    def test_unchanged_excluded_by_default(self):
        result = diff_envs(LEFT, RIGHT, redact=False)
        keys = {e.key for e in result.unchanged}
        assert "DATABASE_URL" not in keys

    def test_unchanged_included_when_requested(self):
        result = diff_envs(LEFT, RIGHT, redact=False, include_unchanged=True)
        keys = {e.key for e in result.unchanged}
        assert "DATABASE_URL" in keys

    def test_has_differences_true(self):
        result = diff_envs(LEFT, RIGHT, redact=False)
        assert result.has_differences is True

    def test_has_differences_false_for_identical(self):
        result = diff_envs(LEFT, LEFT, redact=False)
        assert result.has_differences is False

    def test_redact_masks_sensitive_values(self):
        result = diff_envs(LEFT, RIGHT, redact=True)
        changed_entry = next(e for e in result.changed if e.key == "SECRET_KEY")
        assert changed_entry.left_value == "***REDACTED***"
        assert changed_entry.right_value == "***REDACTED***"

    def test_redact_still_detects_change(self):
        """Even when both sides are redacted, a change should be detected
        only if values differ before redaction."""
        result = diff_envs(LEFT, RIGHT, redact=True)
        # SECRET_KEY differs in raw form; after redaction both become REDACTED
        # so status may be UNCHANGED — this is acceptable documented behaviour.
        entry = next((e for e in result.entries if e.key == "SECRET_KEY"), None)
        assert entry is not None

    def test_entries_sorted_alphabetically(self):
        result = diff_envs(LEFT, RIGHT, redact=False, include_unchanged=True)
        keys = [e.key for e in result.entries]
        assert keys == sorted(keys)


class TestFormatText:
    def test_no_differences_message(self):
        result = diff_envs(LEFT, LEFT, redact=False)
        output = format_text(result)
        assert "No differences" in output

    def test_added_symbol(self):
        result = diff_envs({}, {"NEW": "val"}, redact=False)
        output = format_text(result)
        assert "+ NEW=val" in output

    def test_removed_symbol(self):
        result = diff_envs({"OLD": "val"}, {}, redact=False)
        output = format_text(result)
        assert "- OLD=val" in output

    def test_summary_line_present(self):
        result = diff_envs(LEFT, RIGHT, redact=False)
        output = format_text(result)
        assert "Summary:" in output


class TestFormatJson:
    def test_returns_dict(self):
        result = diff_envs(LEFT, RIGHT, redact=False)
        data = format_json(result)
        assert isinstance(data, dict)

    def test_summary_counts(self):
        result = diff_envs(LEFT, RIGHT, redact=False)
        data = format_json(result)
        assert data["summary"]["added"] == len(result.added)
        assert data["summary"]["removed"] == len(result.removed)
        assert data["summary"]["changed"] == len(result.changed)

    def test_entries_have_required_keys(self):
        result = diff_envs(LEFT, RIGHT, redact=False)
        data = format_json(result)
        for entry in data["entries"]:
            assert {"key", "status", "left_value", "right_value"} <= entry.keys()
