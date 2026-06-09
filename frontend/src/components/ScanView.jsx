import { useState } from "react";
import { api } from "../api.js";

const SAMPLE = `import os, pickle, hashlib

API_KEY = "sk-live-do-not-commit-this"

def run_query(cur, user_id):
    # built from user input — classic injection
    cur.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cur.fetchone()

def load(blob):
    return pickle.loads(blob)

def fingerprint(s):
    return hashlib.md5(s.encode()).hexdigest()

def handle(expr):
    return eval(expr)
`;

export default function ScanView({ engines }) {
  const [code, setCode] = useState(SAMPLE);
  const [engine, setEngine] = useState("ast");
  const [findings, setFindings] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function scan() {
    setBusy(true);
    setError("");
    try {
      const res = await api.analyze(code, engine);
      setFindings(res.findings);
    } catch (e) {
      setError(e.message);
      setFindings(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="view">
      <section className="panel">
        <p className="eyebrow">Scan</p>
        <h2>Paste Python, pick an engine, see what it flags</h2>
        <p className="lede">
          Switch the engine to <code>regex</code> and scan the same code — watch
          it light up on text inside the comment and string that the
          <code> ast</code> engine correctly ignores.
        </p>

        <div className="toolbar">
          <label className="field">
            engine
            <select value={engine} onChange={(e) => setEngine(e.target.value)}>
              {engines.map((eng) => (
                <option key={eng.name} value={eng.name} disabled={!eng.available}>
                  {eng.name}
                  {eng.name === "llm" && !eng.available ? " (needs local Ollama)" : ""}
                </option>
              ))}
            </select>
          </label>
          <span className="grow" />
          <button className="btn btn-ghost" onClick={() => setCode(SAMPLE)}>
            Reset sample
          </button>
          <button className="btn btn-primary" onClick={scan} disabled={busy}>
            {busy ? "Scanning…" : "Scan code"}
          </button>
        </div>

        <textarea
          value={code}
          spellCheck={false}
          onChange={(e) => setCode(e.target.value)}
          aria-label="Python code to scan"
        />

        {error && <div className="error-box">{error}</div>}

        {findings && !error && (
          <div className="findings">
            {findings.length === 0 ? (
              <div className="empty">✓ No issues found by the {engine} engine.</div>
            ) : (
              findings.map((f, i) => (
                <div key={i} className={`finding sev-${f.severity}`}
                     style={{ animationDelay: `${i * 55}ms` }}>
                  <span className="loc">line {f.line}</span>
                  <span className="rid">{f.rule_id}</span>
                  <span className="msg">
                    <strong>{f.title}.</strong> {f.message}
                  </span>
                </div>
              ))
            )}
          </div>
        )}
      </section>
    </div>
  );
}
