"""Tag environment variables by category based on key patterns."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

_TAG_PATTERNS: Dict[str, List[str]] = {
    "database": ["db", "database", "postgres", "mysql", "sqlite", "mongo", "redis"],
    "auth": ["auth", "jwt", "oauth", "token", "secret", "password", "passwd"],
    "network": ["host", "port", "url", "uri", "endpoint", "domain", "addr"],
    "cloud": ["aws", "gcp", "azure", "s3", "bucket", "region", "zone"],
    "logging": ["log", "logging", "sentry", "datadog", "newrelic", "trace"],
    "feature": ["feature", "flag", "enable", "disable", "toggle"],
    "email": ["email", "smtp", "mail", "sendgrid", "mailgun"],
    "api": ["api", "key", "client_id", "client_secret", "webhook"],
}


@dataclass
class TaggedEnv:
    name: str
    tags: Dict[str, List[str]] = field(default_factory=dict)
    untagged: List[str] = field(default_factory=list)

    def all_tags(self) -> List[str]:
        return sorted(self.tags.keys())

    def keys_for_tag(self, tag: str) -> List[str]:
        return self.tags.get(tag, [])

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "tags": {t: sorted(keys) for t, keys in sorted(self.tags.items())},
            "untagged": sorted(self.untagged),
        }

    def __repr__(self) -> str:
        tag_count = len(self.tags)
        key_count = sum(len(v) for v in self.tags.values()) + len(self.untagged)
        return f"TaggedEnv(name={self.name!r}, tags={tag_count}, keys={key_count})"


def _resolve_tag(key: str, patterns: Optional[Dict[str, List[str]]] = None) -> Optional[str]:
    """Return the first matching tag for a key, or None."""
    lower = key.lower()
    resolved = patterns or _TAG_PATTERNS
    for tag, keywords in resolved.items():
        if any(kw in lower for kw in keywords):
            return tag
    return None


def tag_env(
    env: Dict[str, str],
    name: str = "env",
    extra_patterns: Optional[Dict[str, List[str]]] = None,
) -> TaggedEnv:
    """Assign category tags to each key in the environment mapping."""
    patterns = dict(_TAG_PATTERNS)
    if extra_patterns:
        for tag, kws in extra_patterns.items():
            patterns.setdefault(tag, []).extend(kws)

    result: Dict[str, List[str]] = {}
    untagged: List[str] = []

    for key in env:
        tag = _resolve_tag(key, patterns)
        if tag:
            result.setdefault(tag, []).append(key)
        else:
            untagged.append(key)

    return TaggedEnv(name=name, tags=result, untagged=untagged)


def format_tagged_text(tagged: TaggedEnv) -> str:
    """Render a human-readable summary of tagged environment keys."""
    lines = [f"Environment: {tagged.name}"]
    for tag in tagged.all_tags():
        keys = sorted(tagged.keys_for_tag(tag))
        lines.append(f"  [{tag}] ({len(keys)} keys)")
        for k in keys:
            lines.append(f"    - {k}")
    if tagged.untagged:
        lines.append(f"  [untagged] ({len(tagged.untagged)} keys)")
        for k in sorted(tagged.untagged):
            lines.append(f"    - {k}")
    return "\n".join(lines)
