"""Optional LLM detector using a LOCAL model via Ollama.

No paid API. No API key. If Ollama is not installed or not running, this
engine reports itself unavailable and the rest of the app keeps working —
the core scanner and the whole accuracy story rely only on the AST engine.

To enable it locally:
    1. Install Ollama (https://ollama.com) — free, runs on your machine.
    2. `ollama pull qwen2.5-coder:1.5b`   (small, CPU-friendly)
    3. Set OLLAMA_MODEL if you use a different model.

The point of including it is not that the LLM wins — often the AST engine is
more precise on this narrow task. The point is that you *measure* it on the
same dataset and can say exactly where each approach is stronger.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error

from .base import Finding, RULES

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:1.5b")

_RULE_LIST = "\n".join(f"- {rid}: {meta['title']}" for rid, meta in RULES.items())

_PROMPT = """You are a Python security scanner. Find ONLY these issues:
{rules}

Return ONLY a JSON array, no prose. Each item: {{"rule_id": "...", "line": <int>}}.
Use the exact rule_id strings above. If none, return [].

Code (line numbers shown):
{code}
"""


class LlmUnavailable(RuntimeError):
    pass


class LlmDetector:
    name = "llm"
    version = f"ollama:{OLLAMA_MODEL}"

    def available(self) -> bool:
        try:
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=2):
                return True
        except (urllib.error.URLError, OSError):
            return False

    def analyze(self, code: str) -> list[Finding]:
        if not self.available():
            raise LlmUnavailable(
                "Ollama is not running. Start it and pull a model, or use the "
                "ast engine (the default).")
        numbered = "\n".join(f"{i}: {ln}" for i, ln in
                             enumerate(code.splitlines(), start=1))
        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": _PROMPT.format(rules=_RULE_LIST, code=numbered),
            "stream": False,
            "format": "json",
        }).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate", data=payload,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read())
        except (urllib.error.URLError, OSError) as exc:
            raise LlmUnavailable(str(exc)) from exc
        return self._parse(body.get("response", ""))

    @staticmethod
    def _parse(raw: str) -> list[Finding]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if isinstance(data, dict):  # some models wrap it
            data = data.get("findings") or data.get("issues") or []
        out: list[Finding] = []
        for item in data if isinstance(data, list) else []:
            rid = str(item.get("rule_id", "")).strip()
            line = item.get("line")
            if rid in RULES and isinstance(line, int):
                out.append(Finding(rid, line, RULES[rid]["title"]))
        return sorted(set(out), key=lambda f: (f.line, f.rule_id))
