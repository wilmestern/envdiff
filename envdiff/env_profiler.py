"""Profile an environment variable set and produce a structured report."""

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.redactor import is_sensitive


@dataclass
class EnvProfile:
    name: str
    total_keys: int = 0
    sensitive_count: int = 0
    empty_value_count: int = 0
    long_value_count: int = 0
    prefixes: Dict[str, int] = field(default_factory=dict)
    top_prefixes: List[str] = field(default_factory=list)

    LONG_VALUE_THRESHOLD = 128
    TOP_N_PREFIXES = 5

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "total_keys": self.total_keys,
            "sensitive_count": self.sensitive_count,
            "empty_value_count": self.empty_value_count,
            "long_value_count": self.long_value_count,
            "top_prefixes": self.top_prefixes,
        }

    def __repr__(self) -> str:
        return (
            f"EnvProfile(name={self.name!r}, total={self.total_keys}, "
            f"sensitive={self.sensitive_count})"
        )


def _extract_prefix(key: str, sep: str = "_") -> str:
    parts = key.split(sep, 1)
    return parts[0] if len(parts) > 1 else ""


def profile_env(name: str, env: Dict[str, str]) -> EnvProfile:
    """Analyse *env* and return an :class:`EnvProfile`."""
    profile = EnvProfile(name=name)
    profile.total_keys = len(env)

    prefix_counts: Dict[str, int] = {}

    for key, value in env.items():
        if is_sensitive(key):
            profile.sensitive_count += 1
        if value == "":
            profile.empty_value_count += 1
        if len(value) > EnvProfile.LONG_VALUE_THRESHOLD:
            profile.long_value_count += 1
        prefix = _extract_prefix(key)
        if prefix:
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

    profile.prefixes = prefix_counts
    profile.top_prefixes = [
        p
        for p, _ in sorted(prefix_counts.items(), key=lambda x: -x[1])[
            : EnvProfile.TOP_N_PREFIXES
        ]
    ]
    return profile


def format_profile_text(profile: EnvProfile) -> str:
    """Return a human-readable summary of *profile*."""
    lines = [
        f"Profile: {profile.name}",
        f"  Total keys      : {profile.total_keys}",
        f"  Sensitive keys  : {profile.sensitive_count}",
        f"  Empty values    : {profile.empty_value_count}",
        f"  Long values     : {profile.long_value_count}",
    ]
    if profile.top_prefixes:
        lines.append("  Top prefixes    : " + ", ".join(profile.top_prefixes))
    return "\n".join(lines)
