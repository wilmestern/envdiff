import pytest
from envdiff.env_trimmer import (
    TrimResult,
    trim_value,
    trim_env,
    format_trim_text,
)


# ---------------------------------------------------------------------------
# trim_value
# ---------------------------------------------------------------------------

class TestTrimValue:
    def test_strips_leading_whitespace(self):
        assert trim_value("  hello") == "hello"

    def test_strips_trailing_whitespace(self):
        assert trim_value("hello  ") == "hello"

    def test_strips_surrounding_double_quotes(self):
        assert trim_value('"hello"') == "hello"

    def test_strips_surrounding_single_quotes(self):
        assert trim_value("'hello'") == "hello"

    def test_no_strip_quotes_when_disabled(self):
        assert trim_value('"hello"', strip_quotes=False) == '"hello"'

    def test_strips_whitespace_inside_quotes_after_unquote(self):
        assert trim_value('" hello "') == "hello"

    def test_empty_string_unchanged(self):
        assert trim_value("") == ""

    def test_single_char_unchanged(self):
        assert trim_value("x") == "x"

    def test_mismatched_quotes_unchanged(self):
        assert trim_value("'hello\"") == "'hello\""

    def test_already_clean_value_unchanged(self):
        assert trim_value("clean_value") == "clean_value"


# ---------------------------------------------------------------------------
# trim_env
# ---------------------------------------------------------------------------

def _env(**kwargs) -> dict:
    return dict(kwargs)


class TestTrimEnv:
    def test_returns_trim_result(self):
        result = trim_env({"KEY": "value"})
        assert isinstance(result, TrimResult)

    def test_clean_env_has_no_changes(self):
        result = trim_env({"A": "one", "B": "two"})
        assert not result.has_changes()
        assert result.trimmed_keys == []

    def test_detects_whitespace_trimmed_key(self):
        result = trim_env({"KEY": "  value  "})
        assert "KEY" in result.trimmed_keys
        assert result.data["KEY"] == "value"

    def test_detects_quoted_value(self):
        result = trim_env({"KEY": '"quoted"'})
        assert "KEY" in result.trimmed_keys
        assert result.data["KEY"] == "quoted"

    def test_multiple_keys_trimmed(self):
        result = trim_env({"A": " x ", "B": "'y'", "C": "clean"})
        assert set(result.trimmed_keys) == {"A", "B"}
        assert "C" not in result.trimmed_keys

    def test_as_dict_has_expected_keys(self):
        result = trim_env({"K": " v "})
        d = result.as_dict()
        assert "trimmed_keys" in d
        assert "change_count" in d
        assert "data" in d

    def test_repr_contains_change_count(self):
        result = trim_env({"K": " v "})
        assert "change_count=1" in repr(result)

    def test_strip_quotes_disabled(self):
        result = trim_env({"K": '"val"'}, strip_quotes=False)
        assert result.data["K"] == '"val"'
        assert not result.has_changes()


# ---------------------------------------------------------------------------
# format_trim_text
# ---------------------------------------------------------------------------

class TestFormatTrimText:
    def test_no_changes_message(self):
        result = trim_env({"A": "clean"})
        text = format_trim_text(result)
        assert "No values required trimming" in text

    def test_lists_trimmed_keys(self):
        result = trim_env({"FOO": " bar ", "BAZ": "  qux"})
        text = format_trim_text(result)
        assert "FOO" in text
        assert "BAZ" in text

    def test_includes_count(self):
        result = trim_env({"X": " 1 ", "Y": " 2 "})
        text = format_trim_text(result)
        assert "2" in text
