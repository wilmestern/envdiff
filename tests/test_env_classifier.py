"""Tests for envdiff.env_classifier."""

import pytest
from envdiff.env_classifier import (
    ClassifiedEnv,
    _classify_key,
    classify_env,
    format_classification_text,
    OTHER_CATEGORY,
)


def _env(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items()}


class TestClassifyKey:
    def test_database_key(self):
        assert _classify_key("DATABASE_URL") == "database"

    def test_db_prefix(self):
        assert _classify_key("DB_HOST") == "database"

    def test_auth_key(self):
        assert _classify_key("AUTH_TOKEN") == "auth"

    def test_secret_key(self):
        assert _classify_key("APP_SECRET") == "secret"

    def test_network_host(self):
        assert _classify_key("REDIS_HOST") == "database"  # database pattern wins first

    def test_network_port(self):
        assert _classify_key("SERVER_PORT") == "network"

    def test_cloud_aws(self):
        assert _classify_key("AWS_ACCESS_KEY") == "cloud"

    def test_email_smtp(self):
        assert _classify_key("SMTP_HOST") == "email"

    def test_feature_flag(self):
        assert _classify_key("FEATURE_DARK_MODE") == "feature"

    def test_logging_key(self):
        assert _classify_key("LOG_LEVEL") == "logging"

    def test_unknown_key_returns_other(self):
        assert _classify_key("APP_NAME") == OTHER_CATEGORY

    def test_case_insensitive(self):
        assert _classify_key("db_password") == "database"


class TestClassifyEnv:
    def test_empty_env_returns_empty_categories(self):
        result = classify_env({})
        assert result.categories == {}

    def test_name_is_stored(self):
        result = classify_env({}, name="staging")
        assert result.name == "staging"

    def test_default_name(self):
        result = classify_env({})
        assert result.name == "env"

    def test_single_key_classified(self):
        result = classify_env({"DATABASE_URL": "postgres://..."})
        assert "database" in result.categories
        assert "DATABASE_URL" in result.keys_for("database")

    def test_multiple_categories(self):
        env = _env(DATABASE_URL="x", AWS_REGION="us", LOG_LEVEL="info")
        result = classify_env(env)
        assert "database" in result.all_categories()
        assert "cloud" in result.all_categories()
        assert "logging" in result.all_categories()

    def test_unknown_goes_to_other(self):
        result = classify_env({"APP_NAME": "myapp"})
        assert OTHER_CATEGORY in result.categories
        assert "APP_NAME" in result.keys_for(OTHER_CATEGORY)

    def test_as_dict_structure(self):
        env = _env(DATABASE_URL="x", APP_NAME="y")
        d = classify_env(env, name="prod").as_dict()
        assert d["name"] == "prod"
        assert "database" in d["categories"]
        assert "other" in d["categories"]

    def test_repr_contains_name(self):
        result = classify_env({"DB_HOST": "localhost"}, name="dev")
        assert "dev" in repr(result)

    def test_repr_contains_key_count(self):
        result = classify_env({"DB_HOST": "localhost", "APP_NAME": "x"}, name="dev")
        assert "keys=2" in repr(result)


class TestFormatClassificationText:
    def test_includes_name(self):
        result = classify_env({}, name="staging")
        text = format_classification_text(result)
        assert "staging" in text

    def test_includes_category_header(self):
        result = classify_env({"DATABASE_URL": "x"}, name="prod")
        text = format_classification_text(result)
        assert "[database]" in text

    def test_includes_key_name(self):
        result = classify_env({"DATABASE_URL": "x"}, name="prod")
        text = format_classification_text(result)
        assert "DATABASE_URL" in text

    def test_empty_env_produces_header_only(self):
        result = classify_env({}, name="empty")
        text = format_classification_text(result)
        assert text.strip() == "Classification: empty"
