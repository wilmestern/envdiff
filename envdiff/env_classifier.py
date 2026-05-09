"""Classify environment variables into semantic categories based on key patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

# Ordered list of (category, compiled pattern) pairs
_CATEGORY_PATTERNS: List[tuple] = [
    ("database", re.compile(r"(DB|DATABASE|POSTGRES|MYSQL|MONGO|REDIS|SQLITE)", re.I)),
    ("auth", re.compile(r"(AUTH|JWT|OAUTH|SSO|SESSION|COOKIE|CSRF)", re.I)),
    ("secret", re.compile(r"(SECRET|PASSWORD|PASSWD|TOKEN|API_KEY|PRIVATE)", re.I)),
    ("network", re.compile(r"(HOST|PORT|URL|URI|ENDPOINT|DOMAIN|ADDR)", re.I)),
    ("logging", re.compile(r"(LOG|LOGGING|SENTRY|DATADOG|NEWRELIC)", re.I)),
    ("feature", re.compile(r"(FEATURE|FLAG|TOGGLE|ENABLE|DISABLE)", re.I)),
    ("cloud", re.compile(r"(AWS|GCP|AZURE|S3|GCS|BUCKET|REGION|ZONE)", re.I)),
    ("email", re.compile(r"(MAIL|EMAIL|SMTP|SENDGRID|MAILGUN)", re.I)),
]

OTHER_CATEGORY = "other"


@dataclass
class ClassifiedEnv:
    """Result of classifying an environment variable mapping."""

    name: str
    categories: Dict[str, List[str]] = field(default_factory=dict)

    def keys_for(self, category: str) -> List[str]:
        return list(self.categories.get(category, []))

    def all_categories(self) -> List[str]:
        return sorted(self.categories.keys())

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "categories": {k: sorted(v) for k, v in sorted(self.categories.items())},
        }

    def __repr__(self) -> str:
        total = sum(len(v) for v in self.categories.values())
        return f"ClassifiedEnv(name={self.name!r}, keys={total}, categories={self.all_categories()})"


def _classify_key(key: str) -> str:
    for category, pattern in _CATEGORY_PATTERNS:
        if pattern.search(key):
            return category
    return OTHER_CATEGORY


def classify_env(env: Dict[str, str], name: str = "env") -> ClassifiedEnv:
    """Classify all keys in *env* into semantic categories."""
    result: ClassifiedEnv = ClassifiedEnv(name=name)
    for key in env:
        category = _classify_key(key)
        result.categories.setdefault(category, []).append(key)
    return result


def format_classification_text(classified: ClassifiedEnv) -> str:
    """Return a human-readable summary of a ClassifiedEnv."""
    lines = [f"Classification: {classified.name}"]
    for category in classified.all_categories():
        keys = sorted(classified.keys_for(category))
        lines.append(f"  [{category}] ({len(keys)} keys)")
        for k in keys:
            lines.append(f"    {k}")
    return "\n".join(lines)
