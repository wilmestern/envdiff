"""Annotate environment variables with metadata comments."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.redactor import is_sensitive


@dataclass
class AnnotatedEntry:
    key: str
    value: str
    annotations: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "annotations": self.annotations,
        }

    def __repr__(self) -> str:
        tags = ", ".join(self.annotations) if self.annotations else "none"
        return f"<AnnotatedEntry key={self.key!r} annotations=[{tags}]>"


def annotate_env(
    env: Dict[str, str],
    extra_rules: Optional[Dict[str, str]] = None,
) -> List[AnnotatedEntry]:
    """Return a list of AnnotatedEntry objects for each key in *env*.

    Built-in rules:
      - sensitive  : key is considered sensitive by the redactor
      - empty      : value is an empty string
      - numeric    : value is entirely numeric
      - boolean    : value looks like a boolean flag
      - url        : value starts with http:// or https://
    """
    boolean_values = {"true", "false", "yes", "no", "1", "0"}
    results: List[AnnotatedEntry] = []

    for key, value in env.items():
        tags: List[str] = []

        if is_sensitive(key):
            tags.append("sensitive")
        if value == "":
            tags.append("empty")
        if value.lstrip("-").isdigit():
            tags.append("numeric")
        if value.lower() in boolean_values:
            tags.append("boolean")
        if value.startswith(("http://", "https://")):
            tags.append("url")

        if extra_rules:
            for annotation, substring in extra_rules.items():
                if substring.lower() in key.lower() and annotation not in tags:
                    tags.append(annotation)

        results.append(AnnotatedEntry(key=key, value=value, annotations=tags))

    return results


def format_annotations_text(entries: List[AnnotatedEntry]) -> str:
    """Render annotated entries as a human-readable text block."""
    if not entries:
        return "(no entries)"
    lines: List[str] = []
    for entry in entries:
        tag_str = ", ".join(entry.annotations) if entry.annotations else "-"
        lines.append(f"  {entry.key:<30} [{tag_str}]")
    return "\n".join(lines)
