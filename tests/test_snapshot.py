"""Tests for envdiff.snapshot."""

import json
import os
import tempfile

import pytest

from envdiff.snapshot import (
    EnvSnapshot,
    load_snapshot,
    save_snapshot,
    snapshot_from_mapping,
)


class TestEnvSnapshot:
    def test_stores_name_and_data(self):
        s = EnvSnapshot(name="prod", data={"A": "1"})
        assert s.name == "prod"
        assert s.data == {"A": "1"}

    def test_captured_at_is_set_automatically(self):
        s = EnvSnapshot(name="x", data={})
        assert s.captured_at  # non-empty string

    def test_description_defaults_to_none(self):
        s = EnvSnapshot(name="x", data={})
        assert s.description is None

    def test_as_dict_includes_all_fields(self):
        s = EnvSnapshot(name="staging", data={"K": "v"}, description="test snap")
        d = s.as_dict()
        assert d["name"] == "staging"
        assert d["data"] == {"K": "v"}
        assert d["description"] == "test snap"
        assert "captured_at" in d


class TestSaveLoadSnapshot:
    def test_round_trip(self, tmp_path):
        s = EnvSnapshot(name="env", data={"FOO": "bar"}, description="round-trip")
        path = str(tmp_path / "env.json")
        save_snapshot(s, path)
        loaded = load_snapshot(path)
        assert loaded.name == s.name
        assert loaded.data == s.data
        assert loaded.description == s.description
        assert loaded.captured_at == s.captured_at

    def test_file_is_valid_json(self, tmp_path):
        s = EnvSnapshot(name="check", data={"X": "1"})
        path = str(tmp_path / "check.json")
        save_snapshot(s, path)
        with open(path) as fh:
            parsed = json.load(fh)
        assert parsed["name"] == "check"

    def test_save_creates_missing_directories(self, tmp_path):
        path = str(tmp_path / "nested" / "dir" / "snap.json")
        s = EnvSnapshot(name="n", data={})
        save_snapshot(s, path)
        assert os.path.isfile(path)


class TestSnapshotFromMapping:
    def test_creates_snapshot(self):
        s = snapshot_from_mapping("dev", {"A": "1", "B": "2"})
        assert s.name == "dev"
        assert s.data == {"A": "1", "B": "2"}

    def test_copies_mapping(self):
        original = {"A": "1"}
        s = snapshot_from_mapping("x", original)
        original["B"] = "2"
        assert "B" not in s.data

    def test_description_forwarded(self):
        s = snapshot_from_mapping("x", {}, description="hello")
        assert s.description == "hello"
