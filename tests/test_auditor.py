"""Tests for envdiff.auditor."""
import json
import pytest

from envdiff.auditor import AuditEvent, AuditLog, build_audit_event
from envdiff.differ import DiffResult, DiffEntry, DiffStatus


def _make_result(*statuses: DiffStatus) -> DiffResult:
    entries = [
        DiffEntry(status=s, key=f"KEY_{i}", left=None, right=None)
        for i, s in enumerate(statuses)
    ]
    return DiffResult(entries=entries)


class TestBuildAuditEvent:
    def test_counts_added(self):
        result = _make_result(DiffStatus.ADDED, DiffStatus.ADDED)
        event = build_audit_event(result, "staging", "prod")
        assert event.added == 2

    def test_counts_removed(self):
        result = _make_result(DiffStatus.REMOVED)
        event = build_audit_event(result, "staging", "prod")
        assert event.removed == 1

    def test_counts_changed(self):
        result = _make_result(DiffStatus.CHANGED, DiffStatus.CHANGED)
        event = build_audit_event(result, "staging", "prod")
        assert event.changed == 2

    def test_counts_unchanged(self):
        result = _make_result(DiffStatus.UNCHANGED)
        event = build_audit_event(result, "staging", "prod")
        assert event.unchanged == 1

    def test_sources_stored(self):
        result = _make_result()
        event = build_audit_event(result, "left.env", "right.env")
        assert event.left_source == "left.env"
        assert event.right_source == "right.env"

    def test_redacted_flag(self):
        result = _make_result()
        event = build_audit_event(result, "a", "b", redacted=True)
        assert event.redacted is True

    def test_default_redacted_false(self):
        result = _make_result()
        event = build_audit_event(result, "a", "b")
        assert event.redacted is False

    def test_note_stored(self):
        result = _make_result()
        event = build_audit_event(result, "a", "b", note="scheduled audit")
        assert event.note == "scheduled audit"

    def test_timestamp_ends_with_z(self):
        result = _make_result()
        event = build_audit_event(result, "a", "b")
        assert event.timestamp.endswith("Z")


class TestAuditLog:
    def _event(self) -> AuditEvent:
        return build_audit_event(_make_result(DiffStatus.ADDED), "s", "p")

    def test_initially_empty(self):
        log = AuditLog()
        assert len(log) == 0

    def test_record_increases_length(self):
        log = AuditLog()
        log.record(self._event())
        assert len(log) == 1

    def test_as_dict_has_events_key(self):
        log = AuditLog()
        log.record(self._event())
        d = log.as_dict()
        assert "events" in d
        assert len(d["events"]) == 1

    def test_to_json_is_valid_json(self):
        log = AuditLog()
        log.record(self._event())
        parsed = json.loads(log.to_json())
        assert "events" in parsed

    def test_event_as_dict_contains_counts(self):
        result = _make_result(DiffStatus.ADDED, DiffStatus.REMOVED)
        event = build_audit_event(result, "s", "p")
        d = event.as_dict()
        assert d["added"] == 1
        assert d["removed"] == 1
