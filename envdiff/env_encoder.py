"""Encode and decode environment variable mappings to/from portable formats."""

from __future__ import annotations

import base64
import json
from typing import Dict


_ENCODING = "utf-8"


def encode_base64(env: Dict[str, str]) -> str:
    """Encode an env mapping to a base64 JSON string.

    Useful for passing environment configs through channels that only
    support plain text (e.g. CI environment variables, URLs).

    Args:
        env: Mapping of key -> value strings.

    Returns:
        A base64-encoded JSON string.
    """
    payload = json.dumps(env, sort_keys=True, separators=(",", ":"))
    return base64.b64encode(payload.encode(_ENCODING)).decode(_ENCODING)


def decode_base64(encoded: str) -> Dict[str, str]:
    """Decode a base64 JSON string back to an env mapping.

    Args:
        encoded: A base64-encoded JSON string produced by :func:`encode_base64`.

    Returns:
        Mapping of key -> value strings.

    Raises:
        ValueError: If the decoded content is not a valid JSON object whose
            keys and values are all strings.
    """
    try:
        raw = base64.b64decode(encoded.encode(_ENCODING)).decode(_ENCODING)
        data = json.loads(raw)
    except Exception as exc:
        raise ValueError(f"Failed to decode env payload: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Decoded payload is not a JSON object.")

    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError(
                f"All keys and values must be strings; got key={k!r} value={v!r}"
            )

    return data


def encode_hex(env: Dict[str, str]) -> str:
    """Encode an env mapping to a hex JSON string.

    Args:
        env: Mapping of key -> value strings.

    Returns:
        A hex-encoded JSON string.
    """
    payload = json.dumps(env, sort_keys=True, separators=(",", ":"))
    return payload.encode(_ENCODING).hex()


def decode_hex(encoded: str) -> Dict[str, str]:
    """Decode a hex JSON string back to an env mapping.

    Args:
        encoded: A hex-encoded JSON string produced by :func:`encode_hex`.

    Returns:
        Mapping of key -> value strings.

    Raises:
        ValueError: If the decoded content is not a valid JSON object.
    """
    try:
        raw = bytes.fromhex(encoded).decode(_ENCODING)
        data = json.loads(raw)
    except Exception as exc:
        raise ValueError(f"Failed to decode hex env payload: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Decoded payload is not a JSON object.")

    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError(
                f"All keys and values must be strings; got key={k!r} value={v!r}"
            )

    return data
