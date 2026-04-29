"""Tests for the envdiff.redactor module."""

import pytest
from envdiff.redactor import (
    DEFAULT_REDACTED,
    is_sensitive,
    redact_env,
    redact_value,
)


class TestIsSensitive:
    def test_password_key(self):
        assert is_sensitive("DB_PASSWORD") is True

    def test_secret_key(self):
        assert is_sensitive("APP_SECRET") is True

    def test_token_key(self):
        assert is_sensitive("ACCESS_TOKEN") is True

    def test_api_key(self):
        assert is_sensitive("STRIPE_API_KEY") is True

    def test_auth_key(self):
        assert is_sensitive("AUTH_HEADER") is True

    def test_non_sensitive_key(self):
        assert is_sensitive("APP_ENV") is False

    def test_non_sensitive_port(self):
        assert is_sensitive("PORT") is False

    def test_case_insensitive_match(self):
        assert is_sensitive("db_password") is True

    def test_extra_pattern_match(self):
        assert is_sensitive("MY_CERT", extra_patterns=[r"cert"]) is True

    def test_extra_pattern_no_match(self):
        assert is_sensitive("MY_CERT") is False


class TestRedactValue:
    def test_sensitive_value_is_redacted(self):
        assert redact_value("DB_PASSWORD", "supersecret") == DEFAULT_REDACTED

    def test_non_sensitive_value_unchanged(self):
        assert redact_value("APP_ENV", "production") == "production"

    def test_custom_placeholder(self):
        result = redact_value("API_KEY", "abc123", redacted_placeholder="***")
        assert result == "***"

    def test_extra_pattern_redacts(self):
        result = redact_value("MY_CERT", "cert-data", extra_patterns=[r"cert"])
        assert result == DEFAULT_REDACTED


class TestRedactEnv:
    def test_redacts_sensitive_keys(self):
        env = {"DB_PASSWORD": "secret123", "APP_ENV": "staging"}
        result = redact_env(env)
        assert result["DB_PASSWORD"] == DEFAULT_REDACTED
        assert result["APP_ENV"] == "staging"

    def test_original_env_unchanged(self):
        env = {"DB_PASSWORD": "secret123"}
        redact_env(env)
        assert env["DB_PASSWORD"] == "secret123"

    def test_empty_env(self):
        assert redact_env({}) == {}

    def test_all_sensitive(self):
        env = {"TOKEN": "tok", "SECRET": "sec"}
        result = redact_env(env)
        assert all(v == DEFAULT_REDACTED for v in result.values())

    def test_custom_placeholder_applied(self):
        env = {"API_KEY": "key123", "HOST": "localhost"}
        result = redact_env(env, redacted_placeholder="<hidden>")
        assert result["API_KEY"] == "<hidden>"
        assert result["HOST"] == "localhost"
