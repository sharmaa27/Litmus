"""Regex baseline detector.

This exists to be *beaten*. It scans line by line with regular expressions,
which means it has no idea whether a match is real code, a comment, or text
inside a string. Measuring the AST engine against this baseline is the whole
point of the project: it turns "the AST approach is better" from an assertion
into a number.
"""
from __future__ import annotations

import re

from .base import Finding

_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    ("PY-SQL-001", re.compile(r"\.execute\(\s*(f[\"']|.*%|.*\+|.*\.format\()"),
     "Looks like a dynamic query string."),
    ("PY-SECRET-001",
     re.compile(r"(password|passwd|pwd|secret|api_key|apikey|token|access_key|"
                r"private_key)\s*=\s*[\"'].+[\"']", re.IGNORECASE),
     "Credential-like assignment."),
    ("PY-EVAL-001", re.compile(r"\b(eval|exec)\s*\("), "eval/exec call."),
    ("PY-PICKLE-001", re.compile(r"pickle\.(load|loads)\s*\("),
     "pickle deserialization."),
    ("PY-YAML-001", re.compile(r"yaml\.load\s*\("), "yaml.load call."),
    ("PY-SHELL-001", re.compile(r"(os\.system|os\.popen|shell\s*=\s*True)"),
     "Shell execution."),
    ("PY-HASH-001", re.compile(r"hashlib\.(md5|sha1)\s*\("), "Weak hash."),
]


class RegexDetector:
    name = "regex"
    version = "regex-1.0"

    def analyze(self, code: str) -> list[Finding]:
        out: list[Finding] = []
        for i, line in enumerate(code.splitlines(), start=1):
            for rule_id, pattern, msg in _PATTERNS:
                if pattern.search(line):
                    out.append(Finding(rule_id, i, msg))
        return sorted(set(out), key=lambda f: (f.line, f.rule_id))
