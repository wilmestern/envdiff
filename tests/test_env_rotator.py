"""Tests for envdiff.env_rotator."""

from __future__ import annotations

import pytest

from envdiff.baseline import Baseline
from envdiff.env_rotator import RotationEntry, RotationReport, detect_rotations


def _baseline(data: dict, name: str = "prod") -> Baseline:
    return Baseline(name=name, data=data)


# ---------------------------------------------------------------------------
# RotationEntry
# ---------------------------------------------------------------------------

class TestRotationEntry:
    def test_as_dict_includes_key(self):
        entry = RotationEntry(key="HOST", old_value="a", new_value="b")
        assert entry.as_dict()["key"] == "HOST"

    def test_non_sensitive_values_are_plain(self):
        entry = RotationEntry(key="HOST", old_value="old", new_value="new", sensitive=False)
        d = entry.as_dict()
        assert d["old_value"] == "old"
        assert d["new_value"] == "new"

    def test_sensitive_values_are_redacted(self):
        entry = RotationEntry(key="SECRET_KEY", old_value="abc123", new_value="xyz789", sensitive=True)
        d = entry.as_dict()
        assert d["old_value"] != "abc123"
        assert d["new_value"] != "xyz789"
        assert d["sensitive"] is True


# ---------------------------------------------------------------------------
# RotationReport
# ---------------------------------------------------------------------------

class TestRotationReport:
    def test_has_rotations_false_when_empty(self):
        r = RotationReport(name="prod")
        assert r.has_rotations is False

    def test_has_rotations_true_when_entries_present(self):
        r = RotationReport(name="prod", rotated=[RotationEntry("K", "a", "b")])
        assert r.has_rotations is True

    def test_as_dict_contains_name(self):
        r = RotationReport(name="staging")
        assert r.as_dict()["name"] == "staging"

    def test_as_dict_unchanged_sorted(self):
        r = RotationReport(name="x", unchanged=["Z", "A", "M"])
        assert r.as_dict()["unchanged"] == ["A", "M", "Z"]


# ---------------------------------------------------------------------------
# detect_rotations
# ---------------------------------------------------------------------------

class TestDetectRotations:
    def test_detects_changed_value(self):
        b = _baseline({"HOST": "old"})
        report = detect_rotations(b, {"HOST": "new"})
        assert len(report.rotated) == 1
        assert report.rotated[0].key == "HOST"

    def test_unchanged_value_not_in_rotated(self):
        b = _baseline({"HOST": "same"})
        report = detect_rotations(b, {"HOST": "same"})
        assert report.rotated == []
        assert "HOST" in report.unchanged

    def test_detects_added_key(self):
        b = _baseline({})
        report = detect_rotations(b, {"NEW_KEY": "val"})
        assert "NEW_KEY" in report.added

    def test_detects_removed_key(self):
        b = _baseline({"OLD_KEY": "val"})
        report = detect_rotations(b, {})
        assert "OLD_KEY" in report.removed

    def test_sensitive_only_skips_non_sensitive(self):
        b = _baseline({"HOST": "a", "DB_PASSWORD": "old"})
        report = detect_rotations(b, {"HOST": "b", "DB_PASSWORD": "new"}, sensitive_only=True)
        keys = [e.key for e in report.rotated]
        assert "HOST" not in keys
        assert "DB_PASSWORD" in keys

    def test_sensitive_flag_set_for_sensitive_keys(self):
        b = _baseline({"API_TOKEN": "old"})
        report = detect_rotations(b, {"API_TOKEN": "new"})
        assert report.rotated[0].sensitive is True

    def test_non_sensitive_flag_for_plain_keys(self):
        b = _baseline({"APP_HOST": "old"})
        report = detect_rotations(b, {"APP_HOST": "new"})
        assert report.rotated[0].sensitive is False

    def test_report_name_matches_baseline(self):
        b = _baseline({}, name="mybaseline")
        report = detect_rotations(b, {})
        assert report.name == "mybaseline"
