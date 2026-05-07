"""Lint environment variable sets for common issues."""

from dataclasses import dataclass, field
from typing import List, Dict
from envdiff.redactor import is_sensitive


@dataclass
class LintIssue:
    key: str
    message: str
    severity: str = "warning"  # 'warning' or 'error'

    def __repr__(self) -> str:
        return f"LintIssue({self.severity!r}, {self.key!r}: {self.message!r})"

    def as_dict(self) -> dict:
        return {"key": self.key, "message": self.message, "severity": self.severity}


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def as_dict(self) -> dict:
        return {
            "issue_count": len(self.issues),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [i.as_dict() for i in self.issues],
        }


def lint_env(env: Dict[str, str]) -> LintResult:
    """Run all lint checks on an environment variable mapping."""
    issues: List[LintIssue] = []

    for key, value in env.items():
        # Check for empty values on sensitive keys
        if is_sensitive(key) and not value.strip():
            issues.append(LintIssue(key, "Sensitive key has an empty value.", "error"))

        # Check for keys with lowercase letters
        if key != key.upper():
            issues.append(LintIssue(key, "Key contains lowercase letters; prefer ALL_CAPS.", "warning"))

        # Check for keys with spaces
        if " " in key:
            issues.append(LintIssue(key, "Key contains spaces.", "error"))

        # Check for suspiciously short values on non-sensitive keys
        if not is_sensitive(key) and len(value) == 1:
            issues.append(LintIssue(key, "Value is suspiciously short (single character).", "warning"))

        # Check for values that look like unresolved placeholders
        if value.startswith("${") and value.endswith("}"):
            issues.append(LintIssue(key, "Value appears to be an unresolved variable reference.", "warning"))

    return LintResult(issues=issues)


def format_lint_text(result: LintResult, name: str = "") -> str:
    """Format a LintResult as a human-readable string."""
    header = f"Lint results{f' for {name}' if name else ''}"
    lines = [header, "-" * len(header)]
    if not result.has_issues:
        lines.append("No issues found.")
    else:
        for issue in result.issues:
            lines.append(f"  [{issue.severity.upper()}] {issue.key}: {issue.message}")
        lines.append(f"\n{len(result.errors)} error(s), {len(result.warnings)} warning(s).")
    return "\n".join(lines)
