"""Tests for envdiff.baseline."""

import json
from pathlib import Path

import pytest

from envdiff.baseline import (
    Baseline,
    compare_to_baseline,
    load_baseline,
    save_baseline,
)
from envdiff.differ import DiffStatus


SAMPLE_DATA = {"APP_HOST": "localhost", "SECRET_KEY": "abc123", "PORT": "8080"}


class TestBaseline:
    def test_stores_name_and_data(self):
        b = Baseline(name="prod", data=SAMPLE_DATA)
        assert b.name == "prod"
        assert b.data == SAMPLE_DATA

    def test_captured_at_is_set_automatically(self):
        b = Baseline(name="prod", data={})
        assert b.captured_at is not None
        assert "T" in b.captured_at  # ISO format

    def test_description_defaults_to_none(self):
        b = Baseline(name="prod", data={})
        assert b.description is None

    def test_repr_contains_name_and_key_count(self):
        b = Baseline(name="staging", data={"A": "1", "B": "2"})
        r = repr(b)
        assert "staging" in r
        assert "2" in r

    def test_as_dict_includes_all_fields(self):
        b = Baseline(name="prod", data={"X": "1"}, description="golden")
        d = b.as_dict()
        assert d["name"] == "prod"
        assert d["data"] == {"X": "1"}
        assert d["description"] == "golden"
        assert "captured_at" in d

    def test_redacted_hides_sensitive_values(self):
        b = Baseline(name="prod", data={"SECRET_KEY": "topsecret", "APP_HOST": "host"})
        rb = b.redacted()
        assert rb.data["SECRET_KEY"] != "topsecret"
        assert rb.data["APP_HOST"] == "host"

    def test_redacted_preserves_metadata(self):
        b = Baseline(name="prod", data={}, description="desc", captured_at="2024-01-01T00:00:00+00:00")
        rb = b.redacted()
        assert rb.name == b.name
        assert rb.description == b.description
        assert rb.captured_at == b.captured_at


class TestSaveLoadBaseline:
    def test_round_trip(self, tmp_path):
        b = Baseline(name="test", data={"K": "V"}, description="round trip")
        p = tmp_path / "test.json"
        save_baseline(b, p)
        loaded = load_baseline(p)
        assert loaded.name == b.name
        assert loaded.data == b.data
        assert loaded.description == b.description
        assert loaded.captured_at == b.captured_at

    def test_creates_parent_dirs(self, tmp_path):
        p = tmp_path / "nested" / "dir" / "b.json"
        save_baseline(Baseline(name="x", data={}), p)
        assert p.exists()

    def test_saved_file_is_valid_json(self, tmp_path):
        p = tmp_path / "b.json"
        save_baseline(Baseline(name="x", data={"A": "1"}), p)
        raw = json.loads(p.read_text())
        assert raw["name"] == "x"


class TestCompareToBaseline:
    def test_detects_added_key(self):
        base = Baseline(name="b", data={"A": "1"})
        result = compare_to_baseline({"A": "1", "B": "2"}, base)
        statuses = {e.key: e.status for e in result.entries}
        assert statuses["B"] == DiffStatus.ADDED

    def test_detects_removed_key(self):
        base = Baseline(name="b", data={"A": "1", "B": "2"})
        result = compare_to_baseline({"A": "1"}, base)
        statuses = {e.key: e.status for e in result.entries}
        assert statuses["B"] == DiffStatus.REMOVED

    def test_detects_changed_key(self):
        base = Baseline(name="b", data={"A": "old"})
        result = compare_to_baseline({"A": "new"}, base)
        statuses = {e.key: e.status for e in result.entries}
        assert statuses["A"] == DiffStatus.CHANGED
