"""Runs an engine over the whole dataset and records the result.

Every run is appended to eval_history.json. That append-only log is what the
regression dashboard reads: it lets you see whether a change to a detector
actually improved accuracy, or quietly made it worse.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.detectors import get_engine, LlmUnavailable
from app.eval.dataset import load_samples
from app.eval.metrics import score

HISTORY_PATH = Path(__file__).resolve().parent.parent.parent / "eval_history.json"


def run_eval(engine_name: str, note: str = "") -> dict:
    engine = get_engine(engine_name)
    samples = load_samples()
    s = score(samples, engine)
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine": engine_name,
        "version": getattr(engine, "version", engine_name),
        "note": note,
        "samples": len(samples),
        **s.summary(),
    }
    return result


def append_history(result: dict, path: Path = HISTORY_PATH) -> None:
    history = read_history(path)
    history.append(result)
    path.write_text(json.dumps(history, indent=2))


def read_history(path: Path = HISTORY_PATH) -> list[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return []
