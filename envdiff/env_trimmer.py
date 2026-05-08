"""Trim and clean environment variable values.

Provides utilities to strip whitespace, remove surrounding quotes,
and normalize common formatting issues in env values.
"""

from typing import Dict, List, NamedTuple


class TrimResult(NamedTuple):
    """Result of trimming an environment mapping."""

    data: Dict[str, str]
    trimmed_keys: List[str]

    def has_changes(self) -> bool:
        return len(self.trimmed_keys) > 0

    def as_dict(self) -> dict:
        return {
            "trimmed_keys": sorted(self.trimmed_keys),
            "change_count": len(self.trimmed_keys),
            "data": self.data,
        }

    def __repr__(self) -> str:
        return (
            f"TrimResult(change_count={len(self.trimmed_keys)}, "
            f"keys={sorted(self.trimmed_keys)})"
        )


def trim_value(value: str, strip_quotes: bool = True) -> str:
    """Strip leading/trailing whitespace and optionally surrounding quotes."""
    value = value.strip()
    if strip_quotes and len(value) >= 2:
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1].strip()
    return value


def trim_env(
    env: Dict[str, str],
    strip_quotes: bool = True,
) -> TrimResult:
    """Trim all values in an env mapping.

    Returns a TrimResult containing the cleaned data and a list of
    keys whose values were changed.
    """
    cleaned: Dict[str, str] = {}
    trimmed_keys: List[str] = []

    for key, value in env.items():
        new_value = trim_value(value, strip_quotes=strip_quotes)
        cleaned[key] = new_value
        if new_value != value:
            trimmed_keys.append(key)

    return TrimResult(data=cleaned, trimmed_keys=trimmed_keys)


def format_trim_text(result: TrimResult) -> str:
    """Format a TrimResult as a human-readable string."""
    if not result.has_changes():
        return "No values required trimming.\n"

    lines = [f"Trimmed {len(result.trimmed_keys)} value(s):"]
    for key in sorted(result.trimmed_keys):
        lines.append(f"  {key}")
    return "\n".join(lines) + "\n"
