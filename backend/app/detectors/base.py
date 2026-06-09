"""Shared types and the rule registry used by every detector engine.

A Finding is the unit of measurement: (rule_id, line) within a file. Ground
truth in the dataset is expressed in the same shape, so scoring is a direct
set comparison — no fuzzy matching, no judgement calls.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Protocol


@dataclass(frozen=True)
class Finding:
    rule_id: str
    line: int
    message: str

    def key(self) -> tuple[str, int]:
        """The identity used for scoring. A finding is 'the same' as a
        ground-truth label when rule_id and line match."""
        return (self.rule_id, self.line)

    def to_dict(self) -> dict:
        return asdict(self)


# Single source of truth for what the tool looks for. Kept deliberately small:
# every rule below has an objectively checkable right/wrong answer, which is
# what makes the accuracy numbers meaningful.
RULES: dict[str, dict] = {
    "PY-SQL-001": {
        "title": "Possible SQL injection",
        "severity": "high",
        "detail": "A dynamically built string is passed to a database execute call.",
    },
    "PY-SECRET-001": {
        "title": "Hardcoded secret",
        "severity": "high",
        "detail": "A credential-like variable is assigned a string literal.",
    },
    "PY-EVAL-001": {
        "title": "Use of eval/exec",
        "severity": "high",
        "detail": "eval() or exec() runs arbitrary code.",
    },
    "PY-PICKLE-001": {
        "title": "Unsafe deserialization",
        "severity": "high",
        "detail": "pickle.load/loads can execute arbitrary code on untrusted data.",
    },
    "PY-YAML-001": {
        "title": "Unsafe YAML load",
        "severity": "medium",
        "detail": "yaml.load without SafeLoader can construct arbitrary objects.",
    },
    "PY-SHELL-001": {
        "title": "Shell command injection risk",
        "severity": "high",
        "detail": "os.system / shell=True can run injected commands.",
    },
    "PY-HASH-001": {
        "title": "Weak hash algorithm",
        "severity": "low",
        "detail": "md5/sha1 are unsuitable for security-sensitive hashing.",
    },
}


class Detector(Protocol):
    """Every engine implements this. Same input, same output shape, so the
    eval harness can score any of them identically."""

    name: str
    version: str

    def analyze(self, code: str) -> list[Finding]:
        ...
