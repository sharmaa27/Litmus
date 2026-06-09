"""Loads the labeled dataset.

Ground truth is parsed from inline `# EXPECT: RULE-ID` comments, so the labels
live next to the code they describe and cannot drift out of sync. A file with
no annotations is a clean sample: the correct number of findings is zero, and
anything the detector reports on it counts as a false positive.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_EXPECT = re.compile(r"#\s*EXPECT:\s*([A-Z0-9\-]+)")
SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "dataset" / "samples"


@dataclass
class Sample:
    name: str
    code: str
    expected: set[tuple[str, int]]  # (rule_id, line)

    @property
    def is_clean(self) -> bool:
        return not self.expected


def load_samples(samples_dir: Path = SAMPLES_DIR) -> list[Sample]:
    samples: list[Sample] = []
    for path in sorted(samples_dir.glob("*.py")):
        code = path.read_text()
        expected: set[tuple[str, int]] = set()
        for i, line in enumerate(code.splitlines(), start=1):
            for rid in _EXPECT.findall(line):
                expected.add((rid, i))
        samples.append(Sample(path.name, code, expected))
    if not samples:
        raise FileNotFoundError(f"No samples found in {samples_dir}")
    return samples
