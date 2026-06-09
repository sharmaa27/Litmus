"""Engine registry. The eval harness and the API both look engines up here."""
from __future__ import annotations

from .base import Detector, Finding, RULES
from .rules import AstDetector
from .regex_baseline import RegexDetector
from .llm import LlmDetector, LlmUnavailable


def get_engine(name: str) -> Detector:
    engines = {
        "ast": AstDetector,
        "regex": RegexDetector,
        "llm": LlmDetector,
    }
    if name not in engines:
        raise KeyError(f"Unknown engine '{name}'. Choose from {sorted(engines)}.")
    return engines[name]()


ENGINE_NAMES = ["ast", "regex", "llm"]

__all__ = [
    "Detector", "Finding", "RULES", "AstDetector", "RegexDetector",
    "LlmDetector", "LlmUnavailable", "get_engine", "ENGINE_NAMES",
]
