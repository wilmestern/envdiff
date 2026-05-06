"""Tests for envdiff.baseline_store."""

import pytest

from envdiff.baseline import Baseline
from envdiff.baseline_store import BaselineStore


def _make_baseline(name: str = "prod") -> Baseline:
    return Baseline(name=name, data={"APP": "1", "SECRET_KEY": "s3cr3t"})


class TestBaselineStore:
    def test_save_and_load(self, tmp_path):
        store = BaselineStore(tmp_path)
        b = _make_baseline("prod")
        store.save(b)
        loaded = store.load("prod")
        assert loaded.name == b.name
        assert loaded.data == b.data

    def test_exists_true_after_save(self, tmp_path):
        store = BaselineStore(tmp_path)
        store.save(_make_baseline("staging"))
        assert store.exists("staging") is True

    def test_exists_false_before_save(self, tmp_path):
        store = BaselineStore(tmp_path)
        assert store.exists("nope") is False

    def test_list_names_sorted(self, tmp_path):
        store = BaselineStore(tmp_path)
        for name in ["zebra", "alpha", "middle"]:
            store.save(_make_baseline(name))
        assert store.list_names() == ["alpha", "middle", "zebra"]

    def test_list_names_empty_when_no_baselines(self, tmp_path):
        store = BaselineStore(tmp_path)
        assert store.list_names() == []

    def test_load_raises_for_missing_name(self, tmp_path):
        store = BaselineStore(tmp_path)
        with pytest.raises(FileNotFoundError, match="missing"):
            store.load("missing")

    def test_delete_returns_true_when_existed(self, tmp_path):
        store = BaselineStore(tmp_path)
        store.save(_make_baseline("prod"))
        assert store.delete("prod") is True
        assert store.exists("prod") is False

    def test_delete_returns_false_when_not_present(self, tmp_path):
        store = BaselineStore(tmp_path)
        assert store.delete("ghost") is False

    def test_creates_directory_if_missing(self, tmp_path):
        store = BaselineStore(tmp_path / "new" / "dir")
        assert store.directory.exists()

    def test_repr_contains_directory_and_count(self, tmp_path):
        store = BaselineStore(tmp_path)
        store.save(_make_baseline("a"))
        store.save(_make_baseline("b"))
        r = repr(store)
        assert "2" in r
        assert str(tmp_path) in r

    def test_overwrite_existing_baseline(self, tmp_path):
        store = BaselineStore(tmp_path)
        store.save(Baseline(name="prod", data={"K": "old"}))
        store.save(Baseline(name="prod", data={"K": "new"}))
        loaded = store.load("prod")
        assert loaded.data["K"] == "new"
