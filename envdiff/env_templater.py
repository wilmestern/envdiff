"""Generate .env templates from existing env data, replacing values with placeholders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.redactor import is_sensitive


@dataclass
class TemplateEntry:
    key: str
    placeholder: str
    required: bool = True
    comment: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "placeholder": self.placeholder,
            "required": self.required,
            "comment": self.comment,
        }

    def __repr__(self) -> str:
        return f"TemplateEntry(key={self.key!r}, placeholder={self.placeholder!r})"


@dataclass
class EnvTemplate:
    name: str
    entries: List[TemplateEntry] = field(default_factory=list)

    @property
    def keys(self) -> List[str]:
        return [e.key for e in self.entries]

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "entries": [e.as_dict() for e in self.entries],
        }

    def __repr__(self) -> str:
        return f"EnvTemplate(name={self.name!r}, keys={len(self.entries)})"


def _make_placeholder(key: str, sensitive: bool) -> str:
    if sensitive:
        return f"<{key.lower()}_secret>"
    return f"<{key.lower()}>"


def build_template(
    name: str,
    env: Dict[str, str],
    required_keys: Optional[List[str]] = None,
) -> EnvTemplate:
    """Build an EnvTemplate from an env mapping."""
    entries: List[TemplateEntry] = []
    required_set = set(required_keys) if required_keys else set(env.keys())

    for key in sorted(env.keys()):
        sensitive = is_sensitive(key)
        placeholder = _make_placeholder(key, sensitive)
        comment = "sensitive" if sensitive else None
        entries.append(
            TemplateEntry(
                key=key,
                placeholder=placeholder,
                required=key in required_set,
                comment=comment,
            )
        )

    return EnvTemplate(name=name, entries=entries)


def render_template_dotenv(template: EnvTemplate) -> str:
    """Render an EnvTemplate as a .env-style template string."""
    lines: List[str] = [f"# Template: {template.name}", ""]
    for entry in template.entries:
        if entry.comment:
            lines.append(f"# {entry.comment}")
        optional_marker = "" if entry.required else "# optional"
        if optional_marker:
            lines.append(f"# optional")
        lines.append(f"{entry.key}={entry.placeholder}")
    return "\n".join(lines) + "\n"
