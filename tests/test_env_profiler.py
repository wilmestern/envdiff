"""Tests for envdiff.env_profiler."""

import pytest

from envdiff.env_profiler import (
    EnvProfile,
    _extract_prefix,
    profile_env,
    format_profile_text,
)


def _env(**kwargs):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# _extract_prefix
# ---------------------------------------------------------------------------

class TestExtractPrefix:
    def test_returns_prefix_before_first_underscore(self):
        assert _extract_prefix("DB_HOST") == "DB"

    def test_no_underscore_returns_empty(self):
        assert _extract_prefix("HOSTNAME") == ""

    def test_multiple_underscores_returns_first_segment(self):
        assert _extract_prefix("AWS_S3_BUCKET") == "AWS"


# ---------------------------------------------------------------------------
# profile_env
# ---------------------------------------------------------------------------

class TestProfileEnv:
    def test_total_keys_counted(self):
        env = _env(FOO="bar", BAZ="qux")
        p = profile_env("test", env)
        assert p.total_keys == 2

    def test_empty_env_returns_zeros(self):
        p = profile_env("empty", {})
        assert p.total_keys == 0
        assert p.sensitive_count == 0
        assert p.empty_value_count == 0
        assert p.long_value_count == 0

    def test_detects_sensitive_keys(self):
        env = _env(DB_PASSWORD="secret", APP_NAME="myapp", API_KEY="key123")
        p = profile_env("s", env)
        assert p.sensitive_count == 2

    def test_detects_empty_values(self):
        env = _env(FOO="", BAR="", BAZ="present")
        p = profile_env("e", env)
        assert p.empty_value_count == 2

    def test_detects_long_values(self):
        long_val = "x" * 200
        env = _env(BIG="" + long_val, SMALL="tiny")
        p = profile_env("l", env)
        assert p.long_value_count == 1

    def test_value_exactly_at_threshold_is_not_long(self):
        val = "a" * EnvProfile.LONG_VALUE_THRESHOLD
        p = profile_env("t", {"KEY": val})
        assert p.long_value_count == 0

    def test_top_prefixes_ordered_by_frequency(self):
        env = {
            "DB_HOST": "h", "DB_PORT": "5432", "DB_NAME": "mydb",
            "APP_ENV": "prod", "APP_DEBUG": "false",
            "AWS_KEY": "k",
        }
        p = profile_env("multi", env)
        assert p.top_prefixes[0] == "DB"
        assert p.top_prefixes[1] == "APP"

    def test_keys_without_prefix_not_in_top_prefixes(self):
        env = {"HOSTNAME": "host", "PORT": "80"}
        p = profile_env("no_prefix", env)
        assert p.top_prefixes == []

    def test_name_is_stored(self):
        p = profile_env("staging", {})
        assert p.name == "staging"

    def test_repr_contains_name_and_total(self):
        p = profile_env("prod", {"A": "1", "B": "2"})
        r = repr(p)
        assert "prod" in r
        assert "total=2" in r

    def test_as_dict_has_expected_keys(self):
        p = profile_env("x", {"FOO": "bar"})
        d = p.as_dict()
        for key in ("name", "total_keys", "sensitive_count",
                    "empty_value_count", "long_value_count", "top_prefixes"):
            assert key in d


# ---------------------------------------------------------------------------
# format_profile_text
# ---------------------------------------------------------------------------

class TestFormatProfileText:
    def test_contains_name(self):
        p = profile_env("staging", {})
        assert "staging" in format_profile_text(p)

    def test_contains_total_keys(self):
        p = profile_env("x", {"A": "1", "B": "2"})
        text = format_profile_text(p)
        assert "2" in text

    def test_contains_top_prefixes_when_present(self):
        env = {"DB_HOST": "h", "DB_PORT": "5432"}
        p = profile_env("x", env)
        text = format_profile_text(p)
        assert "DB" in text

    def test_no_prefix_line_when_no_prefixes(self):
        p = profile_env("x", {"HOSTNAME": "h"})
        text = format_profile_text(p)
        assert "Top prefixes" not in text
