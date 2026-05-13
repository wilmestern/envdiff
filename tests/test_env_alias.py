"""Tests for envdiff.env_alias."""

import pytest
from envdiff.env_alias import (
    AliasResult,
    apply_aliases,
    find_unresolved,
    invert_aliases,
)


def _env():
    return {"DB_URL": "postgres://localhost/db", "APP_KEY": "secret", "PORT": "8080"}


class TestApplyAliases:
    def test_applies_alias_to_canonical_key(self):
        result = apply_aliases(_env(), {"DATABASE_URL": "DB_URL"})
        assert result.resolved["DATABASE_URL"] == "postgres://localhost/db"

    def test_original_env_unchanged(self):
        env = _env()
        result = apply_aliases(env, {"DATABASE_URL": "DB_URL"})
        assert "DATABASE_URL" not in result.original

    def test_applied_list_contains_canonical_key(self):
        result = apply_aliases(_env(), {"DATABASE_URL": "DB_URL"})
        assert "DATABASE_URL" in result.applied

    def test_missing_alias_source_goes_to_skipped(self):
        result = apply_aliases(_env(), {"DATABASE_URL": "MISSING_KEY"})
        assert "MISSING_KEY" in result.skipped
        assert "DATABASE_URL" not in result.resolved

    def test_does_not_overwrite_existing_canonical_by_default(self):
        env = {**_env(), "DATABASE_URL": "existing"}
        result = apply_aliases(env, {"DATABASE_URL": "DB_URL"})
        assert result.resolved["DATABASE_URL"] == "existing"
        assert "DATABASE_URL" in result.skipped

    def test_overwrite_replaces_existing_canonical(self):
        env = {**_env(), "DATABASE_URL": "existing"}
        result = apply_aliases(env, {"DATABASE_URL": "DB_URL"}, overwrite=True)
        assert result.resolved["DATABASE_URL"] == "postgres://localhost/db"
        assert "DATABASE_URL" in result.applied

    def test_multiple_aliases_applied(self):
        aliases = {"DATABASE_URL": "DB_URL", "SECRET_KEY": "APP_KEY"}
        result = apply_aliases(_env(), aliases)
        assert result.resolved["DATABASE_URL"] == "postgres://localhost/db"
        assert result.resolved["SECRET_KEY"] == "secret"
        assert len(result.applied) == 2

    def test_has_changes_true_when_applied(self):
        result = apply_aliases(_env(), {"DATABASE_URL": "DB_URL"})
        assert result.has_changes() is True

    def test_has_changes_false_when_nothing_applied(self):
        result = apply_aliases(_env(), {"DATABASE_URL": "MISSING"})
        assert result.has_changes() is False

    def test_empty_aliases_returns_original_env(self):
        result = apply_aliases(_env(), {})
        assert result.resolved == _env()
        assert result.applied == []


class TestAliasResult:
    def test_as_dict_has_expected_keys(self):
        result = apply_aliases(_env(), {"DATABASE_URL": "DB_URL"})
        d = result.as_dict()
        assert "applied" in d
        assert "skipped" in d
        assert "resolved_count" in d

    def test_repr_contains_counts(self):
        result = apply_aliases(_env(), {"DATABASE_URL": "DB_URL"})
        r = repr(result)
        assert "applied=1" in r
        assert "skipped=0" in r


class TestInvertAliases:
    def test_inverts_mapping(self):
        aliases = {"DATABASE_URL": "DB_URL", "SECRET_KEY": "APP_KEY"}
        inverted = invert_aliases(aliases)
        assert inverted == {"DB_URL": "DATABASE_URL", "APP_KEY": "SECRET_KEY"}

    def test_empty_returns_empty(self):
        assert invert_aliases({}) == {}


class TestFindUnresolved:
    def test_returns_canonical_keys_with_missing_alias_and_no_canonical(self):
        unresolved = find_unresolved(_env(), {"DATABASE_URL": "MISSING"})
        assert "DATABASE_URL" in unresolved

    def test_does_not_flag_when_canonical_exists(self):
        env = {**_env(), "DATABASE_URL": "value"}
        unresolved = find_unresolved(env, {"DATABASE_URL": "MISSING"})
        assert "DATABASE_URL" not in unresolved

    def test_empty_when_all_aliases_present(self):
        unresolved = find_unresolved(_env(), {"DATABASE_URL": "DB_URL"})
        assert unresolved == []
