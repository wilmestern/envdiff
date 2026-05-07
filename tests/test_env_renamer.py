"""Tests for envdiff.env_renamer."""

import pytest

from envdiff.env_renamer import (
    RenameResult,
    format_rename_text,
    rename_keys,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# TestRenameKeys
# ---------------------------------------------------------------------------

class TestRenameKeys:
    def test_renames_existing_key(self):
        env = _env(OLD_KEY="value")
        new_env, result = rename_keys(env, {"OLD_KEY": "NEW_KEY"})
        assert "NEW_KEY" in new_env
        assert "OLD_KEY" not in new_env
        assert new_env["NEW_KEY"] == "value"

    def test_preserves_value(self):
        env = _env(DB_HOST="localhost")
        new_env, _ = rename_keys(env, {"DB_HOST": "DATABASE_HOST"})
        assert new_env["DATABASE_HOST"] == "localhost"

    def test_skips_missing_key(self):
        env = _env(EXISTING="1")
        new_env, result = rename_keys(env, {"MISSING": "OTHER"})
        assert "MISSING" not in result.renamed
        assert "MISSING" in result.skipped
        assert new_env == env

    def test_conflict_blocks_rename_by_default(self):
        env = _env(OLD="val", NEW="existing")
        new_env, result = rename_keys(env, {"OLD": "NEW"})
        assert "NEW" in result.conflicts
        assert "OLD" in new_env  # original key still present
        assert new_env["NEW"] == "existing"  # target value unchanged

    def test_overwrite_resolves_conflict(self):
        env = _env(OLD="new_val", NEW="old_val")
        new_env, result = rename_keys(env, {"OLD": "NEW"}, overwrite=True)
        assert new_env["NEW"] == "new_val"
        assert "OLD" not in new_env
        assert not result.conflicts

    def test_multiple_renames(self):
        env = _env(A="1", B="2", C="3")
        new_env, result = rename_keys(env, {"A": "X", "B": "Y"})
        assert new_env == {"X": "1", "Y": "2", "C": "3"}
        assert result.renamed == {"A": "X", "B": "Y"}

    def test_original_env_not_mutated(self):
        env = _env(KEY="val")
        original = dict(env)
        rename_keys(env, {"KEY": "NEW_KEY"})
        assert env == original

    def test_rename_to_same_key_is_noop(self):
        env = _env(KEY="val")
        new_env, result = rename_keys(env, {"KEY": "KEY"})
        assert new_env["KEY"] == "val"
        assert result.renamed["KEY"] == "KEY"

    def test_has_conflicts_property(self):
        env = _env(A="1", B="2")
        _, result = rename_keys(env, {"A": "B"})
        assert result.has_conflicts

    def test_has_skipped_property(self):
        env = _env(A="1")
        _, result = rename_keys(env, {"NOPE": "X"})
        assert result.has_skipped

    def test_as_dict_keys(self):
        _, result = rename_keys({}, {})
        d = result.as_dict()
        assert set(d.keys()) == {"renamed", "skipped", "conflicts"}


# ---------------------------------------------------------------------------
# TestFormatRenameText
# ---------------------------------------------------------------------------

class TestFormatRenameText:
    def test_no_renames_returns_default_message(self):
        result = RenameResult()
        assert format_rename_text(result) == "No renames performed."

    def test_shows_renamed_entry(self):
        result = RenameResult(renamed={"OLD": "NEW"})
        text = format_rename_text(result)
        assert "RENAMED" in text
        assert "OLD" in text
        assert "NEW" in text

    def test_shows_skipped_entry(self):
        result = RenameResult(skipped=["MISSING"])
        text = format_rename_text(result)
        assert "SKIPPED" in text
        assert "MISSING" in text

    def test_shows_conflict_entry(self):
        result = RenameResult(conflicts=["TAKEN"])
        text = format_rename_text(result)
        assert "CONFLICT" in text
        assert "TAKEN" in text
