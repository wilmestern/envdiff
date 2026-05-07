"""Score environment variable sets for quality and completeness."""

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.redactor import is_sensitive


@dataclass
class EnvScore:
    """Holds scoring results for an environment variable set."""

    name: str
    total_keys: int
    sensitive_keys: int
    empty_values: int
    long_values: int
    score: float
    penalties: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict:
        return {
            "name": self.name,
            "total_keys": self.total_keys,
            "sensitive_keys": self.sensitive_keys,
            "empty_values": self.empty_values,
            "long_values": self.long_values,
            "score": round(self.score, 2),
            "penalties": self.penalties,
        }

    def __repr__(self) -> str:
        return (
            f"EnvScore(name={self.name!r}, score={self.score:.2f}, "
            f"total_keys={self.total_keys})"
        )


_EMPTY_VALUE_PENALTY = 5.0
_LONG_VALUE_THRESHOLD = 256
_LONG_VALUE_PENALTY = 2.0
_SENSITIVE_EXPOSED_PENALTY = 10.0
_MAX_SCORE = 100.0


def score_env(name: str, env: Dict[str, str]) -> EnvScore:
    """Compute a quality score (0–100) for an env variable mapping."""
    total = len(env)
    penalties: List[str] = []
    deduction = 0.0

    empty = [k for k, v in env.items() if v == ""]
    if empty:
        deduction += len(empty) * _EMPTY_VALUE_PENALTY
        penalties.append(f"{len(empty)} empty value(s): {', '.join(sorted(empty))}")

    long_vals = [k for k, v in env.items() if len(v) > _LONG_VALUE_THRESHOLD]
    if long_vals:
        deduction += len(long_vals) * _LONG_VALUE_PENALTY
        penalties.append(f"{len(long_vals)} overly long value(s)")

    sensitive = [k for k in env if is_sensitive(k)]
    exposed = [k for k in sensitive if env[k] and not env[k].startswith("*")]
    if exposed:
        deduction += len(exposed) * _SENSITIVE_EXPOSED_PENALTY
        penalties.append(f"{len(exposed)} sensitive key(s) with plain-text values")

    raw_score = max(0.0, _MAX_SCORE - deduction)
    normalized = raw_score if total == 0 else min(_MAX_SCORE, raw_score)

    return EnvScore(
        name=name,
        total_keys=total,
        sensitive_keys=len(sensitive),
        empty_values=len(empty),
        long_values=len(long_vals),
        score=normalized,
        penalties=penalties,
    )


def format_score_text(env_score: EnvScore) -> str:
    """Return a human-readable summary of an EnvScore."""
    lines = [
        f"Score for '{env_score.name}': {env_score.score:.1f}/100",
        f"  Total keys   : {env_score.total_keys}",
        f"  Sensitive    : {env_score.sensitive_keys}",
        f"  Empty values : {env_score.empty_values}",
        f"  Long values  : {env_score.long_values}",
    ]
    if env_score.penalties:
        lines.append("  Penalties:")
        for p in env_score.penalties:
            lines.append(f"    - {p}")
    return "\n".join(lines)
