"""Tests for envdiff.drift_detector."""

from __future__ import annotations

import pytest

from envdiff.baseline import Baseline
from envdiff.drift_detector import DriftReport, detect_drift


def _make_baseline(data: dict, name: str = "prod") -> Baseline:
    return Baseline(name=name, data=data)


class TestDriftReport:
    def test_no_drift_when_empty(self):
        report = DriftReport(baseline_name="prod")
        assert report.has_drift is False

    def test_has_drift_when_added(self):
        from envdiff.differ import DiffEntry, DiffStatus

        entry = DiffEntry(key="NEW_KEY", status=DiffStatus.ADDED, left=None, right="v")
        report = DriftReport(baseline_name="prod", added=[entry])
        assert report.has_drift is True

    def test_total_changes_sums_all_categories(self):
        from envdiff.differ import DiffEntry, DiffStatus

        a = DiffEntry(key="A", status=DiffStatus.ADDED, left=None, right="1")
        r = DiffEntry(key="B", status=DiffStatus.REMOVED, left="2", right=None)
        c = DiffEntry(key="C", status=DiffStatus.CHANGED, left="x", right="y")
        report = DriftReport(baseline_name="prod", added=[a], removed=[r], changed=[c])
        assert report.total_changes == 3

    def test_as_dict_keys(self):
        report = DriftReport(baseline_name="staging")
        d = report.as_dict()
        assert set(d.keys()) == {
            "baseline_name",
            "has_drift",
            "total_changes",
            "added",
            "removed",
            "changed",
        }

    def test_as_dict_baseline_name(self):
        report = DriftReport(baseline_name="staging")
        assert report.as_dict()["baseline_name"] == "staging"


class TestDetectDrift:
    def test_no_drift_when_identical(self):
        data = {"HOST": "localhost", "PORT": "5432"}
        baseline = _make_baseline(data)
        report = detect_drift(current=data, baseline=baseline)
        assert report.has_drift is False

    def test_detects_added_key(self):
        baseline = _make_baseline({"HOST": "localhost"})
        current = {"HOST": "localhost", "NEW_KEY": "value"}
        report = detect_drift(current=current, baseline=baseline)
        assert len(report.added) == 1
        assert report.added[0].key == "NEW_KEY"

    def test_detects_removed_key(self):
        baseline = _make_baseline({"HOST": "localhost", "OLD_KEY": "gone"})
        current = {"HOST": "localhost"}
        report = detect_drift(current=current, baseline=baseline)
        assert len(report.removed) == 1
        assert report.removed[0].key == "OLD_KEY"

    def test_detects_changed_key(self):
        baseline = _make_baseline({"HOST": "old-host"})
        current = {"HOST": "new-host"}
        report = detect_drift(current=current, baseline=baseline)
        assert len(report.changed) == 1
        assert report.changed[0].key == "HOST"

    def test_baseline_name_preserved(self):
        baseline = _make_baseline({}, name="production")
        report = detect_drift(current={}, baseline=baseline)
        assert report.baseline_name == "production"

    def test_redact_flag_uses_redacted_baseline(self):
        """With redact=True, sensitive baseline values are masked before compare."""
        baseline = _make_baseline({"SECRET_KEY": "mysecret", "HOST": "prod"})
        # current has the same HOST but a different (unredacted) SECRET_KEY value
        current = {"SECRET_KEY": "mysecret", "HOST": "prod"}
        report = detect_drift(current=current, baseline=baseline, redact=True)
        # SECRET_KEY in baseline becomes REDACTED, so it differs from current
        assert any(e.key == "SECRET_KEY" for e in report.changed)

    def test_as_dict_lists_key_names(self):
        baseline = _make_baseline({"A": "1", "B": "2"})
        current = {"A": "changed", "C": "new"}
        report = detect_drift(current=current, baseline=baseline)
        d = report.as_dict()
        assert "A" in d["changed"]
        assert "B" in d["removed"]
        assert "C" in d["added"]
