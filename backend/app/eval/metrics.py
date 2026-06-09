"""Scoring. A finding is identified by (rule_id, line); ground truth uses the
same key, so true/false positives and false negatives are plain set algebra —
nothing subjective enters the numbers."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Score:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    per_rule: dict[str, dict[str, int]] = field(default_factory=dict)
    # Findings we got wrong, kept so the UI can show "here is where it fails".
    false_positives: list[dict] = field(default_factory=list)
    false_negatives: list[dict] = field(default_factory=list)

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    def summary(self) -> dict:
        return {
            "tp": self.tp, "fp": self.fp, "fn": self.fn,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "per_rule": self.per_rule,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
        }


def score(samples, engine) -> Score:
    s = Score()
    rule_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"tp": 0, "fp": 0, "fn": 0})

    for sample in samples:
        found = {f.key() for f in engine.analyze(sample.code)
                 if f.rule_id != "PARSE-ERROR"}
        truth = sample.expected

        for key in found & truth:
            s.tp += 1
            rule_counts[key[0]]["tp"] += 1
        for key in found - truth:
            s.fp += 1
            rule_counts[key[0]]["fp"] += 1
            s.false_positives.append(
                {"sample": sample.name, "rule_id": key[0], "line": key[1]})
        for key in truth - found:
            s.fn += 1
            rule_counts[key[0]]["fn"] += 1
            s.false_negatives.append(
                {"sample": sample.name, "rule_id": key[0], "line": key[1]})

    s.per_rule = dict(rule_counts)
    return s
