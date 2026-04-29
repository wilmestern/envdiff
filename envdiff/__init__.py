"""envdiff — Compare environment variable sets with redaction support."""

from envdiff.parser import parse_env_file, parse_env_string, parse_env_mapping
from envdiff.redactor import redact_env, redact_value, is_sensitive

__all__ = [
    "parse_env_file",
    "parse_env_string",
    "parse_env_mapping",
    "redact_env",
    "redact_value",
    "is_sensitive",
]

__version__ = "0.1.0"
