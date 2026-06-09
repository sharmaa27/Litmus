"""FastAPI surface for the scanner.

Endpoints:
    GET  /api/health           liveness
    GET  /api/rules            the rule catalogue
    GET  /api/engines          engines and whether each is available
    POST /api/analyze          scan a snippet with a chosen engine
    POST /api/eval/run         run the accuracy eval, log it, return the result
    GET  /api/eval/history     the append-only history for the dashboard
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.detectors import (RULES, ENGINE_NAMES, get_engine, LlmDetector,
                           LlmUnavailable)
from app.eval.runner import run_eval, append_history, read_history

app = FastAPI(title="Litmus", version="1.0",
              description="A Python security scanner that measures its own accuracy.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    code: str = Field(..., max_length=50_000)
    engine: str = Field("ast")


class EvalRequest(BaseModel):
    engine: str = Field("ast")
    note: str = Field("", max_length=200)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/rules")
def rules() -> dict:
    return {"rules": [{"id": rid, **meta} for rid, meta in RULES.items()]}


@app.get("/api/engines")
def engines() -> dict:
    out = []
    for name in ENGINE_NAMES:
        available = True
        if name == "llm":
            available = LlmDetector().available()
        out.append({"name": name, "available": available})
    return {"engines": out}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    try:
        engine = get_engine(req.engine)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        findings = engine.analyze(req.code)
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "engine": req.engine,
        "findings": [
            {**f.to_dict(), **_rule_meta(f.rule_id)} for f in findings
        ],
    }


@app.post("/api/eval/run")
def eval_run(req: EvalRequest) -> dict:
    try:
        result = run_eval(req.engine, note=req.note)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    append_history(result)
    return result


@app.get("/api/eval/history")
def eval_history() -> dict:
    return {"history": read_history()}


def _rule_meta(rule_id: str) -> dict:
    meta = RULES.get(rule_id)
    if not meta:
        return {"title": rule_id, "severity": "info"}
    return {"title": meta["title"], "severity": meta["severity"]}
