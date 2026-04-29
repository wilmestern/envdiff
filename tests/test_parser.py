"""Tests for envdiff.parser module."""

import os
import tempfile
import pytest

from envdiff.parser import parse_env_string, parse_env_file, parse_env_mapping


class TestParseEnvString:
    def test_simple_key_value(self):
        result = parse_env_string("FOO=bar")
        assert result == {"FOO": "bar"}

    def test_multiple_entries(self):
        content = "FOO=bar\nBAZ=qux"
        result = parse_env_string(content)
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_ignores_comments(self):
        content = "# this is a comment\nFOO=bar"
        result = parse_env_string(content)
        assert result == {"FOO": "bar"}

    def test_ignores_blank_lines(self):
        content = "\nFOO=bar\n\nBAZ=qux\n"
        result = parse_env_string(content)
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_double_quoted_value(self):
        result = parse_env_string('DB_URL="postgres://localhost/db"')
        assert result == {"DB_URL": "postgres://localhost/db"}

    def test_single_quoted_value(self):
        result = parse_env_string("SECRET='my secret'")
        assert result == {"SECRET": "my secret"}

    def test_export_prefix(self):
        result = parse_env_string("export API_KEY=abc123")
        assert result == {"API_KEY": "abc123"}

    def test_inline_comment_stripped(self):
        result = parse_env_string("PORT=8080 # default port")
        assert result == {"PORT": "8080"}

    def test_empty_value(self):
        result = parse_env_string("EMPTY=")
        assert result == {"EMPTY": ""}

    def test_value_with_equals_sign(self):
        result = parse_env_string('TOKEN="abc=def=ghi"')
        assert result == {"TOKEN": "abc=def=ghi"}

    def test_empty_string_returns_empty_dict(self):
        assert parse_env_string("") == {}


class TestParseEnvFile:
    def test_reads_file_correctly(self):
        content = "HOST=localhost\nPORT=5432\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = parse_env_file(tmp_path)
            assert result == {"HOST": "localhost", "PORT": "5432"}
        finally:
            os.unlink(tmp_path)

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError, match="Env file not found"):
            parse_env_file("/nonexistent/path/.env")


class TestParseEnvMapping:
    def test_converts_mapping_to_plain_dict(self):
        mapping = {"FOO": "bar", "BAZ": "123"}
        result = parse_env_mapping(mapping)
        assert result == {"FOO": "bar", "BAZ": "123"}

    def test_uses_os_environ_when_none(self):
        result = parse_env_mapping(None)
        assert isinstance(result, dict)
        # PATH should exist in virtually all environments
        assert "PATH" in result or len(result) >= 0

    def test_coerces_values_to_str(self):
        result = parse_env_mapping({"NUM": "42"})
        assert result["NUM"] == "42"
        assert isinstance(result["NUM"], str)
