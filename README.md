# Litmus

**A static security scanner for a fixed set of Python mistakes — that measures and reports its own accuracy instead of asking you to trust it.**

Most "AI code reviewer" projects emit findings and stop there. The interesting
question is never *"can it produce output?"* — anything can. The question is
*"is the output correct, and how do you know?"* Litmus answers that out loud:
it scores itself on a labeled dataset and shows precision, recall, and a list
of exactly what it gets wrong.

React + FastAPI + Docker. **No paid APIs** — the core runs on Python's standard
library; the optional LLM engine runs locally via Ollama.

---

## What it does

- Scans pasted Python for a small, well-defined set of security issues
  (SQL injection, hardcoded secrets, `eval`/`exec`, unsafe `pickle`/`yaml`,
  shell injection, weak hashing).
- Runs that detection through three interchangeable engines and **measures
  each one on the same labeled dataset**:
  - `regex` — a deliberately naive line-by-line baseline (built to be beaten).
  - `ast` — the primary engine; parses a syntax tree, so it never fires on
    text inside comments or strings.
  - `llm` — optional, local-only via Ollama. Often *less* precise here; the
    point is that you can measure that rather than assume it.
- Logs every evaluation to an append-only history so you can see whether a
  change to a detector improved accuracy or quietly regressed it.

## The measured result (current)

Scored on 24 labeled samples, matching findings by exact `(rule, line)`:

| engine | precision | recall | F1 |
|--------|-----------|--------|----|
| regex baseline | 78.3% | 94.7% | 85.7% |
| **AST (primary)** | **94.7%** | **94.7%** | **94.7%** |

The AST engine's precision win comes entirely from *not* firing inside
comments and string literals, and from understanding `yaml.load(...,
Loader=SafeLoader)` as safe — three false positives the regex baseline can't
avoid because it cannot see structure.

## Where it fails (on purpose, documented)

Honesty is the feature, so the failures are first-class:

- **One false positive:** a variable named `default_token` holding a harmless
  literal (`"<PAD>"`) is flagged as a hardcoded secret. The name heuristic
  can't tell a credential from an unfortunately-named constant.
- **One false negative (both engines):** an injectable query built by string
  concatenation on one line and passed to `execute()` on the next is missed,
  because neither engine tracks data flow. Catching it would require taint
  analysis — the natural next step, and the reason real tools are far more
  complex than this.

These are the kinds of limitations the metrics make visible. Without the
dataset, you'd never know they were there.

## Design decisions (and why)

- **Scope narrowed to objectively checkable rules.** "Code quality" can't be
  measured; "is there an `eval()` call on line 12" can. A measurable scope is
  the whole reason the accuracy numbers mean anything.
- **Ground truth lives in the samples.** Each vulnerable line carries an inline
  `# EXPECT: RULE-ID` comment, so labels can't drift out of sync with the code
  and the detectors (which read the AST, not comments) can't cheat off them.
- **AST over regex as the primary engine.** Chosen because it's measurably more
  precise — see the table. The regex engine is kept specifically to prove that
  claim with a number rather than an assertion.
- **Local LLM, not a paid API.** Keeps the project free to run and reproducible,
  and reframes the LLM as one more engine to *evaluate* rather than trust.

## Run it

### With Docker (recommended)

```bash
docker compose up --build
```

- App: http://localhost:8080
- API docs: http://localhost:8000/docs

### Without Docker

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000
```

Frontend (separate terminal):
```bash
cd frontend
npm install
npm run dev                            # http://localhost:5173
```

### Run the evaluation from the CLI

```bash
cd backend
python run_eval.py all                 # score every engine
python run_eval.py ast --note "tuned secret heuristic"
```

### Run the tests

```bash
cd backend
pip install pytest
pytest
```

## Optional: enable the local LLM engine

No account or key needed.

1. Install [Ollama](https://ollama.com) (free).
2. `ollama pull qwen2.5-coder:1.5b`
3. Restart the backend. The `llm` engine becomes selectable; if Ollama isn't
   running, the app simply marks it unavailable and everything else works.

## Project layout

```
backend/
  app/detectors/     regex, ast, and llm engines (same interface)
  app/eval/          dataset loader, metrics, run/history logger
  dataset/samples/   labeled .py samples (ground truth inline)
  run_eval.py        CLI scorer
frontend/
  src/components/    ScanView, CalibrationView (the metrics signature)
docker-compose.yml
```

## What I would do next

- Add taint/data-flow tracking to close the cross-line injection blind spot.
- Expand the dataset (more samples per rule) so per-rule precision/recall is
  statistically meaningful, not just directional.
- Hold out a test split so tuning can't overfit to the samples being scored.
```
