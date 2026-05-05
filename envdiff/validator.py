"""Validator module for checking env var sets against rules and schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str = "error"  # "error" or "warning"

    def __repr__(self) -> str:
        return f"ValidationIssue({self.severity}: {self.key!r} — {self.message})"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def validate_required_keys(
    env: Dict[str, str],
    required_keys: List[str],
) -> List[ValidationIssue]:
    """Return issues for any required keys missing from env."""
    issues = []
    for key in required_keys:
        if key not in env:
            issues.append(
                ValidationIssue(key=key, message=f"Required key '{key}' is missing.", severity="error")
            )
    return issues


def validate_no_empty_values(
    env: Dict[str, str],
    warn_only: bool = False,
) -> List[ValidationIssue]:
    """Return issues for keys whose values are empty strings."""
    severity = "warning" if warn_only else "error"
    issues = []
    for key, value in env.items():
        if value == "":
            issues.append(
                ValidationIssue(key=key, message=f"Key '{key}' has an empty value.", severity=severity)
            )
    return issues


def validate_env(
    env: Dict[str, str],
    required_keys: Optional[List[str]] = None,
    warn_empty: bool = False,
    error_empty: bool = False,
) -> ValidationResult:
    """Run all configured validations against an env mapping."""
    issues: List[ValidationIssue] = []

    if required_keys:
        issues.extend(validate_required_keys(env, required_keys))

    if warn_empty:
        issues.extend(validate_no_empty_values(env, warn_only=True))
    elif error_empty:
        issues.extend(validate_no_empty_values(env, warn_only=False))

    return ValidationResult(issues=issues)
