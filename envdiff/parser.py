"""Parser for .env files and environment variable dictionaries."""

import os
import re
from typing import Dict, Optional


ENV_LINE_PATTERN = re.compile(
    r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$'
)


def parse_env_string(content: str) -> Dict[str, str]:
    """Parse a .env file string into a dictionary of key-value pairs.

    Handles:
    - Comments (lines starting with #)
    - Blank lines
    - Quoted values (single and double quotes)
    - export prefix
    - Inline comments (after unquoted values)
    """
    result: Dict[str, str] = {}

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        match = ENV_LINE_PATTERN.match(stripped)
        if not match:
            continue

        key, value = match.group(1), match.group(2)
        value = _parse_value(value)
        result[key] = value

    return result


def _parse_value(raw: str) -> str:
    """Strip quotes and inline comments from a raw env value."""
    raw = raw.strip()

    if (raw.startswith('"') and raw.endswith('"')) or \
       (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]

    # Strip inline comment for unquoted values
    comment_match = re.search(r'\s+#.*$', raw)
    if comment_match:
        raw = raw[:comment_match.start()]

    return raw.strip()


def parse_env_file(filepath: str) -> Dict[str, str]:
    """Read and parse a .env file from disk."""
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Env file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as fh:
        return parse_env_string(fh.read())


def parse_env_mapping(mapping: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Normalize an existing dictionary (e.g. os.environ) into a plain dict."""
    if mapping is None:
        mapping = dict(os.environ)
    return {str(k): str(v) for k, v in mapping.items()}
