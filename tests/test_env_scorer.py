"""Tests for envdiff.env_scorer."""

import pytest

from envdiff.env_scorer import EnvScore, score_env, format_score_text


def _env(**kwargs):
    return dict(kwargs)


class TestScoreEnv:
    def test_empty_env_returns_perfect_score(self):
        result = score_env("test", {})
        assert result.score == 100.0

    def test_name_is_stored(self):
        result = score_env("staging", {})
        assert result.name == "staging"

    def test_total_keys_counted(self):
        result = score_env("x", _env(A="1", B="2"))
        assert result.total_keys == 2

    def test_empty_value_causes_penalty(self):
        result = score_env("x", _env(FOO=""))
        assert result.score < 100.0
        assert result.empty_values == 1

    def test_multiple_empty_values_stack_penalty(self):
        result = score_env("x", _env(A="", B="", C=""))
        assert result.empty_values == 3
        assert result.score <= 85.0

    def test_empty_value_penalty_in_penalties_list(self):
        result = score_env("x", _env(FOO=""))
        assert any("empty" in p for p in result.penalties)

    def test_long_value_causes_penalty(self):
        long_val = "x" * 300
        result = score_env("x", _env(BIG=long_val))
        assert result.long_values == 1
        assert result.score < 100.0

    def test_sensitive_key_with_plain_text_causes_penalty(self):
        result = score_env("x", _env(DB_PASSWORD="secret123"))
        assert result.sensitive_keys >= 1
        assert result.score < 100.0
        assert any("sensitive" in p for p in result.penalties)

    def test_sensitive_key_already_redacted_no_penalty(self):
        result = score_env("x", _env(DB_PASSWORD="***"))
        # redacted values start with '*', no plain-text penalty
        plain_penalties = [p for p in result.penalties if "sensitive" in p]
        assert plain_penalties == []

    def test_score_does_not_go_below_zero(self):
        env = {f"SECRET_{i}": "plaintext" for i in range(20)}
        result = score_env("x", env)
        assert result.score >= 0.0

    def test_score_does_not_exceed_100(self):
        result = score_env("x", _env(NORMAL_KEY="value"))
        assert result.score <= 100.0

    def test_as_dict_contains_expected_keys(self):
        result = score_env("prod", _env(A="1"))
        d = result.as_dict()
        assert set(d.keys()) == {
            "name", "total_keys", "sensitive_keys",
            "empty_values", "long_values", "score", "penalties",
        }

    def test_as_dict_score_is_rounded(self):
        result = score_env("x", {})
        d = result.as_dict()
        assert isinstance(d["score"], float)

    def test_repr_contains_name_and_score(self):
        result = score_env("staging", {})
        r = repr(result)
        assert "staging" in r
        assert "100.00" in r


class TestFormatScoreText:
    def test_contains_name(self):
        s = score_env("staging", _env(A="1"))
        text = format_score_text(s)
        assert "staging" in text

    def test_contains_score_value(self):
        s = score_env("prod", {})
        text = format_score_text(s)
        assert "100.0" in text

    def test_penalties_section_shown_when_present(self):
        s = score_env("x", _env(FOO=""))
        text = format_score_text(s)
        assert "Penalties" in text

    def test_no_penalties_section_when_clean(self):
        s = score_env("x", _env(APP_ENV="production"))
        text = format_score_text(s)
        assert "Penalties" not in text
