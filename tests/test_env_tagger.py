"""Tests for envdiff.env_tagger."""

import pytest
from envdiff.env_tagger import (
    TaggedEnv,
    _resolve_tag,
    tag_env,
    format_tagged_text,
)


def _env(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items()}


# ---------------------------------------------------------------------------
# _resolve_tag
# ---------------------------------------------------------------------------

class TestResolveTag:
    def test_database_key(self):
        assert _resolve_tag("DATABASE_URL") == "database"

    def test_auth_key(self):
        assert _resolve_tag("AUTH_TOKEN") == "auth"

    def test_network_host(self):
        assert _resolve_tag("REDIS_HOST") == "network"

    def test_unrecognised_returns_none(self):
        assert _resolve_tag("FOOBAR_XYZ") is None

    def test_case_insensitive(self):
        assert _resolve_tag("Smtp_Host") is not None

    def test_custom_patterns_override(self):
        patterns = {"custom": ["foobar"]}
        assert _resolve_tag("FOOBAR_KEY", patterns) == "custom"


# ---------------------------------------------------------------------------
# tag_env
# ---------------------------------------------------------------------------

class TestTagEnv:
    def test_returns_tagged_env_instance(self):
        result = tag_env({}, name="test")
        assert isinstance(result, TaggedEnv)

    def test_name_is_stored(self):
        result = tag_env({}, name="staging")
        assert result.name == "staging"

    def test_database_key_tagged(self):
        result = tag_env({"DATABASE_URL": "postgres://localhost/db"})
        assert "DATABASE_URL" in result.keys_for_tag("database")

    def test_unrecognised_key_goes_to_untagged(self):
        result = tag_env({"FOOBAR_XYZ": "value"})
        assert "FOOBAR_XYZ" in result.untagged

    def test_multiple_tags_populated(self):
        env = {"DB_HOST": "localhost", "AUTH_TOKEN": "abc", "SMTP_HOST": "mail"}
        result = tag_env(env)
        assert len(result.all_tags()) >= 2

    def test_extra_patterns_extend_defaults(self):
        env = {"MYAPP_FEATURE": "on"}
        result = tag_env(env, extra_patterns={"custom": ["myapp"]})
        assert "MYAPP_FEATURE" in result.keys_for_tag("custom")

    def test_as_dict_contains_expected_keys(self):
        result = tag_env({"DB_HOST": "localhost"}, name="prod")
        d = result.as_dict()
        assert "name" in d and "tags" in d and "untagged" in d

    def test_repr_contains_name(self):
        result = tag_env({}, name="staging")
        assert "staging" in repr(result)

    def test_all_tags_sorted(self):
        env = {"AUTH_TOKEN": "x", "DATABASE_URL": "y", "SMTP_HOST": "z"}
        result = tag_env(env)
        tags = result.all_tags()
        assert tags == sorted(tags)


# ---------------------------------------------------------------------------
# format_tagged_text
# ---------------------------------------------------------------------------

class TestFormatTaggedText:
    def test_contains_env_name(self):
        tagged = tag_env({}, name="production")
        text = format_tagged_text(tagged)
        assert "production" in text

    def test_contains_tag_header(self):
        tagged = tag_env({"AUTH_SECRET": "abc"}, name="env")
        text = format_tagged_text(tagged)
        assert "[auth]" in text

    def test_contains_key_name(self):
        tagged = tag_env({"AUTH_SECRET": "abc"}, name="env")
        text = format_tagged_text(tagged)
        assert "AUTH_SECRET" in text

    def test_untagged_section_present(self):
        tagged = tag_env({"TOTALLY_UNKNOWN_XYZ": "val"}, name="env")
        text = format_tagged_text(tagged)
        assert "untagged" in text
