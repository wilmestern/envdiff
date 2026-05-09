"""Tests for envdiff.env_encoder."""

import pytest

from envdiff.env_encoder import (
    decode_base64,
    decode_hex,
    encode_base64,
    encode_hex,
)


_SAMPLE: dict = {"APP_ENV": "production", "DB_HOST": "db.example.com", "PORT": "5432"}


# ---------------------------------------------------------------------------
# encode_base64 / decode_base64
# ---------------------------------------------------------------------------


class TestBase64RoundTrip:
    def test_encode_returns_string(self):
        result = encode_base64(_SAMPLE)
        assert isinstance(result, str)

    def test_decode_restores_original(self):
        encoded = encode_base64(_SAMPLE)
        assert decode_base64(encoded) == _SAMPLE

    def test_empty_env_roundtrips(self):
        assert decode_base64(encode_base64({})) == {}

    def test_special_characters_in_value(self):
        env = {"SECRET": "p@$$w0rd!=#&"}
        assert decode_base64(encode_base64(env)) == env

    def test_output_is_stable_for_same_input(self):
        """Encoding is deterministic (keys sorted)."""
        assert encode_base64(_SAMPLE) == encode_base64(_SAMPLE)

    def test_different_envs_produce_different_output(self):
        other = {"APP_ENV": "staging"}
        assert encode_base64(_SAMPLE) != encode_base64(other)


class TestDecodeBase64Errors:
    def test_invalid_base64_raises_value_error(self):
        with pytest.raises(ValueError, match="Failed to decode"):
            decode_base64("!!!not-base64!!!")

    def test_base64_non_object_raises_value_error(self):
        import base64, json
        encoded = base64.b64encode(json.dumps([1, 2, 3]).encode()).decode()
        with pytest.raises(ValueError, match="not a JSON object"):
            decode_base64(encoded)

    def test_non_string_value_raises_value_error(self):
        import base64, json
        payload = json.dumps({"KEY": 42})
        encoded = base64.b64encode(payload.encode()).decode()
        with pytest.raises(ValueError, match="must be strings"):
            decode_base64(encoded)


# ---------------------------------------------------------------------------
# encode_hex / decode_hex
# ---------------------------------------------------------------------------


class TestHexRoundTrip:
    def test_encode_returns_string(self):
        result = encode_hex(_SAMPLE)
        assert isinstance(result, str)

    def test_decode_restores_original(self):
        encoded = encode_hex(_SAMPLE)
        assert decode_hex(encoded) == _SAMPLE

    def test_empty_env_roundtrips(self):
        assert decode_hex(encode_hex({})) == {}

    def test_hex_output_contains_only_hex_chars(self):
        encoded = encode_hex(_SAMPLE)
        assert all(c in "0123456789abcdef" for c in encoded)

    def test_output_is_stable_for_same_input(self):
        assert encode_hex(_SAMPLE) == encode_hex(_SAMPLE)


class TestDecodeHexErrors:
    def test_invalid_hex_raises_value_error(self):
        with pytest.raises(ValueError, match="Failed to decode"):
            decode_hex("zzzz")

    def test_hex_non_object_raises_value_error(self):
        import json
        encoded = json.dumps(["a", "b"]).encode().hex()
        with pytest.raises(ValueError, match="not a JSON object"):
            decode_hex(encoded)

    def test_non_string_key_raises_value_error(self):
        import json
        payload = json.dumps({"KEY": 99})
        encoded = payload.encode().hex()
        with pytest.raises(ValueError, match="must be strings"):
            decode_hex(encoded)
