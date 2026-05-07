"""Tests for envdiff.env_grouper."""

import pytest

from envdiff.env_grouper import EnvGroup, format_groups_text, group_by_prefix


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "mydb",
        "AWS_ACCESS_KEY": "AKIA...",
        "AWS_SECRET_KEY": "secret",
        "PORT": "8080",
        "DEBUG": "true",
    }


# ---------------------------------------------------------------------------
# TestEnvGroup
# ---------------------------------------------------------------------------


class TestEnvGroup:
    def test_stores_name_and_keys(self):
        g = EnvGroup(name="DB", keys=["DB_HOST", "DB_PORT"])
        assert g.name == "DB"
        assert "DB_HOST" in g.keys

    def test_as_dict_sorts_keys(self):
        g = EnvGroup(name="DB", keys=["DB_PORT", "DB_HOST"])
        d = g.as_dict()
        assert d["keys"] == ["DB_HOST", "DB_PORT"]
        assert d["name"] == "DB"

    def test_default_keys_is_empty_list(self):
        g = EnvGroup(name="X")
        assert g.keys == []


# ---------------------------------------------------------------------------
# TestGroupByPrefix
# ---------------------------------------------------------------------------


class TestGroupByPrefix:
    def test_groups_by_first_segment(self):
        groups = group_by_prefix(_env())
        assert "DB" in groups
        assert "AWS" in groups

    def test_db_group_has_correct_keys(self):
        groups = group_by_prefix(_env())
        assert set(groups["DB"].keys) == {"DB_HOST", "DB_PORT", "DB_NAME"}

    def test_keys_without_separator_go_to_other(self):
        groups = group_by_prefix(_env())
        other = groups.get("OTHER")
        assert other is not None
        assert "PORT" in other.keys
        assert "DEBUG" in other.keys

    def test_custom_ungrouped_label(self):
        groups = group_by_prefix(_env(), ungrouped_label="MISC")
        assert "MISC" in groups
        assert "PORT" in groups["MISC"].keys

    def test_min_group_size_merges_small_groups(self):
        env = {"A_ONE": "1", "B_ONE": "2", "B_TWO": "3"}
        groups = group_by_prefix(env, min_group_size=2)
        # A has only 1 key, should be merged into OTHER
        assert "A" not in groups
        assert "B" in groups
        assert "A_ONE" in groups["OTHER"].keys

    def test_custom_separator(self):
        env = {"DB.HOST": "h", "DB.PORT": "p", "APP.NAME": "n"}
        groups = group_by_prefix(env, separator=".")
        assert "DB" in groups
        assert "APP" in groups

    def test_empty_env_returns_empty(self):
        groups = group_by_prefix({})
        assert groups == {}


# ---------------------------------------------------------------------------
# TestFormatGroupsText
# ---------------------------------------------------------------------------


class TestFormatGroupsText:
    def test_contains_group_header(self):
        groups = group_by_prefix({"DB_HOST": "localhost", "DB_PORT": "5432"})
        text = format_groups_text(groups)
        assert "[DB]" in text

    def test_shows_key_count(self):
        groups = group_by_prefix({"DB_HOST": "h", "DB_PORT": "p"})
        text = format_groups_text(groups)
        assert "2 keys" in text

    def test_shows_values_when_env_provided(self):
        env = {"DB_HOST": "localhost"}
        groups = group_by_prefix(env)
        text = format_groups_text(groups, env=env)
        assert "localhost" in text

    def test_redacts_sensitive_values(self):
        env = {"DB_PASSWORD": "s3cret"}
        groups = group_by_prefix(env)
        text = format_groups_text(groups, env=env, redact=True)
        assert "s3cret" not in text
        assert "DB_PASSWORD" in text
