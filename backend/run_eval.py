#!/usr/bin/env python3
"""Run the accuracy evaluation from the command line.

Examples:
    python run_eval.py ast              # score the AST engine, log result
    python run_eval.py regex            # score the regex baseline
    python run_eval.py ast --no-log     # score without writing history
    python run_eval.py all              # score every available engine
"""
import argparse
import json

from app.detectors import ENGINE_NAMES, LlmUnavailable
from app.eval.runner import run_eval, append_history


def _run_one(name: str, log: bool, note: str) -> None:
    try:
        result = run_eval(name, note=note)
    except LlmUnavailable as exc:
        print(f"[{name}] skipped: {exc}")
        return
    print(f"[{result['engine']}] "
          f"precision={result['precision']:.3f}  "
          f"recall={result['recall']:.3f}  "
          f"f1={result['f1']:.3f}  "
          f"(tp={result['tp']} fp={result['fp']} fn={result['fn']}, "
          f"{result['samples']} samples)")
    if result["false_positives"]:
        print("  false positives:",
              ", ".join(f"{fp['sample']}:{fp['line']} {fp['rule_id']}"
                        for fp in result["false_positives"]))
    if result["false_negatives"]:
        print("  false negatives:",
              ", ".join(f"{fn['sample']}:{fn['line']} {fn['rule_id']}"
                        for fn in result["false_negatives"]))
    if log:
        append_history(result)


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the security-scanner eval.")
    ap.add_argument("engine", choices=ENGINE_NAMES + ["all"])
    ap.add_argument("--no-log", action="store_true", help="don't write history")
    ap.add_argument("--note", default="", help="label this run in the history")
    args = ap.parse_args()

    names = ENGINE_NAMES if args.engine == "all" else [args.engine]
    for name in names:
        _run_one(name, log=not args.no_log, note=args.note)


if __name__ == "__main__":
    main()
