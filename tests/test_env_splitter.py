"""Tests for envdiff.env_splitter."""

import pytest

from envdiff.env_splitter import EnvSplit, split_by_keys, split_by_prefixes


def _env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "AWS_KEY": "AKIA123",
        "AWS_SECRET": "s3cr3t",
        "APP_DEBUG": "true",
        "LOG_LEVEL": "info",
    }


# ---------------------------------------------------------------------------
# EnvSplit dataclass
# ---------------------------------------------------------------------------

class TestEnvSplit:
    def test_stores_name_and_data(self):
        s = EnvSplit(name="db", data={"DB_HOST": "localhost"})
        assert s.name == "db"
        assert s.data == {"DB_HOST": "localhost"}

    def test_as_dict_has_expected_keys(self):
        s = EnvSplit(name="db", data={"DB_HOST": "localhost"})
        d = s.as_dict()
        assert set(d.keys()) == {"name", "keys", "data"}

    def test_as_dict_sorts_keys(self):
        s = EnvSplit(name="x", data={"Z": "1", "A": "2"})
        assert s.as_dict()["keys"] == ["A", "Z"]

    def test_default_data_is_empty(self):
        s = EnvSplit(name="empty")
        assert s.data == {}


# ---------------------------------------------------------------------------
# split_by_prefixes
# ---------------------------------------------------------------------------

class TestSplitByPrefixes:
    def test_groups_db_keys(self):
        result = split_by_prefixes(_env(), ["DB_", "AWS_"])
        db = next(s for s in result if s.name == "DB_")
        assert set(db.data.keys()) == {"DB_HOST", "DB_PORT"}

    def test_groups_aws_keys(self):
        result = split_by_prefixes(_env(), ["DB_", "AWS_"])
        aws = next(s for s in result if s.name == "AWS_")
        assert set(aws.data.keys()) == {"AWS_KEY", "AWS_SECRET"}

    def test_remainder_collects_unmatched(self):
        result = split_by_prefixes(_env(), ["DB_", "AWS_"])
        other = next(s for s in result if s.name == "other")
        assert set(other.data.keys()) == {"APP_DEBUG", "LOG_LEVEL"}

    def test_no_remainder_when_name_is_none(self):
        result = split_by_prefixes(_env(), ["DB_"], remainder_name=None)
        names = [s.name for s in result]
        assert "other" not in names
        assert len(result) == 1

    def test_case_insensitive_by_default(self):
        env = {"db_host": "localhost", "db_port": "5432"}
        result = split_by_prefixes(env, ["DB_"])
        db = next(s for s in result if s.name == "DB_")
        assert set(db.data.keys()) == {"db_host", "db_port"}

    def test_case_sensitive_mode(self):
        env = {"db_host": "localhost", "DB_PORT": "5432"}
        result = split_by_prefixes(env, ["DB_"], case_sensitive=True)
        db = next(s for s in result if s.name == "DB_")
        assert "DB_PORT" in db.data
        assert "db_host" not in db.data

    def test_first_matching_prefix_wins(self):
        env = {"DB_HOST": "localhost"}
        result = split_by_prefixes(env, ["DB_", "DB_H"])
        first = next(s for s in result if s.name == "DB_")
        second = next(s for s in result if s.name == "DB_H")
        assert "DB_HOST" in first.data
        assert "DB_HOST" not in second.data


# ---------------------------------------------------------------------------
# split_by_keys
# ---------------------------------------------------------------------------

class TestSplitByKeys:
    def test_assigns_keys_to_named_groups(self):
        result = split_by_keys(_env(), {"database": ["DB_HOST", "DB_PORT"]})
        db = next(s for s in result if s.name == "database")
        assert set(db.data.keys()) == {"DB_HOST", "DB_PORT"}

    def test_missing_keys_silently_skipped(self):
        result = split_by_keys(_env(), {"x": ["NONEXISTENT"]})
        x = next(s for s in result if s.name == "x")
        assert x.data == {}

    def test_remainder_captures_unassigned(self):
        result = split_by_keys(_env(), {"database": ["DB_HOST", "DB_PORT"]})
        other = next(s for s in result if s.name == "other")
        assert "AWS_KEY" in other.data

    def test_no_remainder_when_name_is_none(self):
        result = split_by_keys(_env(), {"database": ["DB_HOST"]}, remainder_name=None)
        names = [s.name for s in result]
        assert "other" not in names
