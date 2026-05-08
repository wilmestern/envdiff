"""Tests for envdiff.env_annotator."""
from __future__ import annotations

import pytest

from envdiff.env_annotator import AnnotatedEntry, annotate_env, format_annotations_text


def _env(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# AnnotatedEntry
# ---------------------------------------------------------------------------

class TestAnnotatedEntry:
    def test_as_dict_has_expected_keys(self):
        entry = AnnotatedEntry(key="FOO", value="bar", annotations=["numeric"])
        d = entry.as_dict()
        assert set(d.keys()) == {"key", "value", "annotations"}

    def test_repr_contains_key(self):
        entry = AnnotatedEntry(key="FOO", value="bar", annotations=["url"])
        assert "FOO" in repr(entry)

    def test_repr_contains_annotations(self):
        entry = AnnotatedEntry(key="X", value="y", annotations=["sensitive", "empty"])
        assert "sensitive" in repr(entry)

    def test_default_annotations_empty(self):
        entry = AnnotatedEntry(key="K", value="v")
        assert entry.annotations == []


# ---------------------------------------------------------------------------
# annotate_env
# ---------------------------------------------------------------------------

class TestAnnotateEnv:
    def test_empty_env_returns_empty_list(self):
        assert annotate_env({}) == []

    def test_sensitive_key_tagged(self):
        entries = annotate_env(_env(DB_PASSWORD="secret"))
        assert "sensitive" in entries[0].annotations

    def test_empty_value_tagged(self):
        entries = annotate_env(_env(FOO=""))
        assert "empty" in entries[0].annotations

    def test_numeric_value_tagged(self):
        entries = annotate_env(_env(PORT="8080"))
        assert "numeric" in entries[0].annotations

    def test_negative_numeric_tagged(self):
        entries = annotate_env(_env(OFFSET="-5"))
        assert "numeric" in entries[0].annotations

    def test_boolean_true_tagged(self):
        entries = annotate_env(_env(DEBUG="true"))
        assert "boolean" in entries[0].annotations

    def test_boolean_yes_tagged(self):
        entries = annotate_env(_env(ENABLED="yes"))
        assert "boolean" in entries[0].annotations

    def test_url_value_tagged(self):
        entries = annotate_env(_env(API_URL="https://example.com"))
        assert "url" in entries[0].annotations

    def test_http_url_tagged(self):
        entries = annotate_env(_env(ENDPOINT="http://localhost"))
        assert "url" in entries[0].annotations

    def test_plain_value_has_no_tags(self):
        entries = annotate_env(_env(APP_NAME="myapp"))
        assert entries[0].annotations == []

    def test_multiple_keys_returned_in_order(self):
        env = {"ALPHA": "1", "BETA": "two", "GAMMA": ""}
        entries = annotate_env(env)
        assert [e.key for e in entries] == ["ALPHA", "BETA", "GAMMA"]

    def test_extra_rules_applied(self):
        entries = annotate_env(_env(REDIS_HOST="localhost"), extra_rules={"cache": "redis"})
        assert "cache" in entries[0].annotations

    def test_extra_rules_case_insensitive_key_match(self):
        entries = annotate_env(_env(REDIS_URL="redis://host"), extra_rules={"cache": "REDIS"})
        assert "cache" in entries[0].annotations

    def test_extra_rule_not_applied_when_no_match(self):
        entries = annotate_env(_env(APP_NAME="myapp"), extra_rules={"cache": "redis"})
        assert "cache" not in entries[0].annotations


# ---------------------------------------------------------------------------
# format_annotations_text
# ---------------------------------------------------------------------------

class TestFormatAnnotationsText:
    def test_empty_list_returns_placeholder(self):
        assert format_annotations_text([]) == "(no entries)"

    def test_key_appears_in_output(self):
        entries = [AnnotatedEntry(key="MY_KEY", value="v", annotations=["numeric"])]
        assert "MY_KEY" in format_annotations_text(entries)

    def test_annotation_appears_in_output(self):
        entries = [AnnotatedEntry(key="X", value="", annotations=["empty"])]
        assert "empty" in format_annotations_text(entries)

    def test_no_annotations_shows_dash(self):
        entries = [AnnotatedEntry(key="PLAIN", value="val", annotations=[])]
        assert "-" in format_annotations_text(entries)
