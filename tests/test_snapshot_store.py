"""Tests for envdiff.snapshot_store and envdiff.snapshot_diff."""

import pytest

from envdiff.snapshot import EnvSnapshot
from envdiff.snapshot_diff import diff_snapshots, snapshot_summary_line
from envdiff.snapshot_store import SnapshotStore


class TestSnapshotStore:
    def test_save_and_load(self, tmp_path):
        store = SnapshotStore(str(tmp_path))
        s = EnvSnapshot(name="prod", data={"KEY": "val"})
        store.save(s)
        loaded = store.load("prod")
        assert loaded.data == {"KEY": "val"}

    def test_exists_true_after_save(self, tmp_path):
        store = SnapshotStore(str(tmp_path))
        s = EnvSnapshot(name="staging", data={})
        store.save(s)
        assert store.exists("staging")

    def test_exists_false_before_save(self, tmp_path):
        store = SnapshotStore(str(tmp_path))
        assert not store.exists("missing")

    def test_list_names_sorted(self, tmp_path):
        store = SnapshotStore(str(tmp_path))
        for name in ["beta", "alpha", "gamma"]:
            store.save(EnvSnapshot(name=name, data={}))
        assert store.list_names() == ["alpha", "beta", "gamma"]

    def test_len(self, tmp_path):
        store = SnapshotStore(str(tmp_path))
        assert len(store) == 0
        store.save(EnvSnapshot(name="a", data={}))
        assert len(store) == 1

    def test_iter_yields_snapshots(self, tmp_path):
        store = SnapshotStore(str(tmp_path))
        store.save(EnvSnapshot(name="x", data={"V": "1"}))
        store.save(EnvSnapshot(name="y", data={"V": "2"}))
        names = [s.name for s in store]
        assert sorted(names) == ["x", "y"]

    def test_creates_directory_if_missing(self, tmp_path):
        import os
        new_dir = str(tmp_path / "new" / "store")
        store = SnapshotStore(new_dir)
        assert os.path.isdir(new_dir)


class TestDiffSnapshots:
    def _snap(self, name, data):
        return EnvSnapshot(name=name, data=data)

    def test_detects_added_key(self):
        before = self._snap("before", {"A": "1"})
        after = self._snap("after", {"A": "1", "B": "2"})
        result = diff_snapshots(before, after)
        keys = [e.key for e in result.entries]
        assert "B" in keys

    def test_detects_removed_key(self):
        before = self._snap("before", {"A": "1", "B": "2"})
        after = self._snap("after", {"A": "1"})
        result = diff_snapshots(before, after)
        keys = [e.key for e in result.entries]
        assert "B" in keys

    def test_detects_changed_key(self):
        before = self._snap("before", {"A": "old"})
        after = self._snap("after", {"A": "new"})
        result = diff_snapshots(before, after)
        assert len(result.entries) == 1
        assert result.entries[0].key == "A"

    def test_no_diff_on_identical(self):
        snap = self._snap("same", {"A": "1"})
        result = diff_snapshots(snap, snap)
        assert len(result.entries) == 0


class TestSnapshotSummaryLine:
    def test_summary_format(self):
        before = EnvSnapshot(name="v1", data={"A": "1", "B": "2"})
        after = EnvSnapshot(name="v2", data={"A": "changed", "C": "3"})
        line = snapshot_summary_line(before, after)
        assert "v1" in line
        assert "v2" in line
        assert "+1" in line   # C added
        assert "-1" in line   # B removed
        assert "~1" in line   # A changed
