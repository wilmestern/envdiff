"""Tests for envdiff.env_templater."""

from __future__ import annotations

import pytest

from envdiff.env_templater import (
    TemplateEntry,
    EnvTemplate,
    build_template,
    render_template_dotenv,
    _make_placeholder,
)


def _env(**kwargs) -> dict:
    return dict(kwargs)


class TestTemplateEntry:
    def test_defaults_to_required(self):
        entry = TemplateEntry(key="FOO", placeholder="<foo>")
        assert entry.required is True

    def test_comment_defaults_to_none(self):
        entry = TemplateEntry(key="FOO", placeholder="<foo>")
        assert entry.comment is None

    def test_repr_contains_key_and_placeholder(self):
        entry = TemplateEntry(key="FOO", placeholder="<foo>")
        assert "FOO" in repr(entry)
        assert "<foo>" in repr(entry)

    def test_as_dict_has_all_fields(self):
        entry = TemplateEntry(key="FOO", placeholder="<foo>", required=False, comment="hi")
        d = entry.as_dict()
        assert d["key"] == "FOO"
        assert d["placeholder"] == "<foo>"
        assert d["required"] is False
        assert d["comment"] == "hi"


class TestEnvTemplate:
    def test_keys_returns_all_keys(self):
        t = EnvTemplate(name="test", entries=[
            TemplateEntry("A", "<a>"),
            TemplateEntry("B", "<b>"),
        ])
        assert t.keys == ["A", "B"]

    def test_repr_contains_name_and_count(self):
        t = EnvTemplate(name="prod", entries=[TemplateEntry("X", "<x>")])
        assert "prod" in repr(t)
        assert "1" in repr(t)

    def test_as_dict_has_entries(self):
        t = EnvTemplate(name="prod", entries=[TemplateEntry("X", "<x>")])
        d = t.as_dict()
        assert d["name"] == "prod"
        assert len(d["entries"]) == 1


class TestMakePlaceholder:
    def test_sensitive_key_includes_secret(self):
        ph = _make_placeholder("DB_PASSWORD", sensitive=True)
        assert "secret" in ph

    def test_non_sensitive_key_no_secret(self):
        ph = _make_placeholder("APP_HOST", sensitive=False)
        assert "secret" not in ph
        assert "app_host" in ph


class TestBuildTemplate:
    def test_all_keys_included(self):
        env = _env(FOO="1", BAR="2")
        t = build_template("test", env)
        assert set(t.keys) == {"FOO", "BAR"}

    def test_keys_sorted(self):
        env = _env(ZEBRA="z", ALPHA="a")
        t = build_template("test", env)
        assert t.keys == ["ALPHA", "ZEBRA"]

    def test_sensitive_entry_has_comment(self):
        env = {"DB_PASSWORD": "secret123"}
        t = build_template("test", env)
        assert t.entries[0].comment == "sensitive"

    def test_non_sensitive_entry_has_no_comment(self):
        env = {"APP_HOST": "localhost"}
        t = build_template("test", env)
        assert t.entries[0].comment is None

    def test_required_keys_subset(self):
        env = _env(FOO="1", BAR="2", BAZ="3")
        t = build_template("test", env, required_keys=["FOO"])
        required = {e.key for e in t.entries if e.required}
        assert required == {"FOO"}

    def test_all_required_by_default(self):
        env = _env(FOO="1", BAR="2")
        t = build_template("test", env)
        assert all(e.required for e in t.entries)


class TestRenderTemplateDotenv:
    def test_contains_template_name(self):
        t = build_template("staging", {"HOST": "x"})
        output = render_template_dotenv(t)
        assert "staging" in output

    def test_contains_key_and_placeholder(self):
        t = build_template("test", {"APP_HOST": "x"})
        output = render_template_dotenv(t)
        assert "APP_HOST=" in output
        assert "<app_host>" in output

    def test_sensitive_key_has_comment_line(self):
        t = build_template("test", {"DB_PASSWORD": "secret"})
        output = render_template_dotenv(t)
        assert "# sensitive" in output

    def test_ends_with_newline(self):
        t = build_template("test", {"X": "1"})
        output = render_template_dotenv(t)
        assert output.endswith("\n")
