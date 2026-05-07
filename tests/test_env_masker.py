"""Tests for envdiff.env_masker."""

import pytest

from envdiff.env_masker import MaskStyle, mask_env, mask_value


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

class TestMaskValueFull:
    def test_returns_placeholder(self):
        assert mask_value("supersecret", style=MaskStyle.FULL) == "***"

    def test_custom_placeholder(self):
        assert mask_value("abc", style=MaskStyle.FULL, placeholder="[hidden]") == "[hidden]"

    def test_empty_string_unchanged(self):
        assert mask_value("", style=MaskStyle.FULL) == ""


class TestMaskValueLength:
    def test_same_length_as_input(self):
        result = mask_value("hello", style=MaskStyle.LENGTH)
        assert len(result) == 5

    def test_all_mask_chars(self):
        result = mask_value("hello", style=MaskStyle.LENGTH)
        assert result == "*****"

    def test_custom_mask_char(self):
        result = mask_value("hi", style=MaskStyle.LENGTH, mask_char="#")
        assert result == "##"

    def test_empty_string_unchanged(self):
        assert mask_value("", style=MaskStyle.LENGTH) == ""


class TestMaskValuePartial:
    def test_reveals_first_four_chars(self):
        result = mask_value("abcdefgh", style=MaskStyle.PARTIAL)
        assert result.startswith("abcd")

    def test_masks_remainder(self):
        result = mask_value("abcdefgh", style=MaskStyle.PARTIAL)
        assert result == "abcd****"

    def test_short_value_fully_masked(self):
        result = mask_value("abc", style=MaskStyle.PARTIAL, reveal_chars=4)
        assert result == "***"

    def test_exact_reveal_length_fully_masked(self):
        result = mask_value("abcd", style=MaskStyle.PARTIAL, reveal_chars=4)
        assert result == "****"

    def test_custom_reveal_chars(self):
        result = mask_value("abcdefgh", style=MaskStyle.PARTIAL, reveal_chars=2)
        assert result == "ab******"


# ---------------------------------------------------------------------------
# mask_env
# ---------------------------------------------------------------------------

class TestMaskEnv:
    def test_sensitive_key_is_masked(self):
        env = {"DB_PASSWORD": "s3cr3t", "APP_NAME": "myapp"}
        result = mask_env(env)
        assert result["DB_PASSWORD"] == "***"

    def test_non_sensitive_key_unchanged(self):
        env = {"DB_PASSWORD": "s3cr3t", "APP_NAME": "myapp"}
        result = mask_env(env)
        assert result["APP_NAME"] == "myapp"

    def test_original_env_not_mutated(self):
        env = {"API_KEY": "original"}
        mask_env(env)
        assert env["API_KEY"] == "original"

    def test_partial_style_applied_to_sensitive(self):
        env = {"SECRET_TOKEN": "abcdefgh"}
        result = mask_env(env, style=MaskStyle.PARTIAL)
        assert result["SECRET_TOKEN"] == "abcd****"

    def test_length_style_applied_to_sensitive(self):
        env = {"AUTH_SECRET": "hello"}
        result = mask_env(env, style=MaskStyle.LENGTH)
        assert result["AUTH_SECRET"] == "*****"

    def test_empty_env_returns_empty(self):
        assert mask_env({}) == {}

    def test_all_non_sensitive_keys_pass_through(self):
        env = {"HOST": "localhost", "PORT": "5432"}
        result = mask_env(env)
        assert result == env
