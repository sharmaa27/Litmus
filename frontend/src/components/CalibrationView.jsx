import { useEffect, useState, useRef } from "react";
import { api } from "../api.js";

const pct = (x) => `${(x * 100).toFixed(1)}%`;

// Count a number up from 0 to target once, respecting reduced-motion.
function useCountUp(target, duration = 900) {
  const [val, setVal] = useState(target);
  useEffect(() => {
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduce) { setVal(target); return; }
    const start = performance.now();
    let raf;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setVal(target * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return val;
}

function RingGauge({ label, value, color }) {
  const animated = useCountUp(value);
  const R = 42, C = 2 * Math.PI * R;
  const offset = C * (1 - value);
  return (
    <div className="gauge">
      <svg viewBox="0 0 110 110" width="118" height="118">
        <circle className="ring-track" cx="55" cy="55" r={R} fill="none" strokeWidth="9" />
        <circle
          cx="55" cy="55" r={R} fill="none" stroke={color} strokeWidth="9"
          strokeLinecap="round" strokeDasharray={C} strokeDashoffset={offset}
          transform="rotate(-90 55 55)"
          style={{ transition: "stroke-dashoffset 1s cubic-bezier(0.22,1,0.36,1)" }}
        />
        <text className="center-v" x="55" y="62" textAnchor="middle">
          {(animated * 100).toFixed(1)}%
        </text>
      </svg>
      <div className="k">{label}</div>
    </div>
  );
}

function Trend({ history }) {
  if (history.length < 1) return null;
  const w = 660, h = 150, pad = 26;
  const n = history.length;
  const x = (i) => (n === 1 ? w / 2 : pad + (i * (w - 2 * pad)) / (n - 1));
  const y = (v) => h - pad - v * (h - 2 * pad);
  const path = (key) => history.map((r, i) => `${i ? "L" : "M"}${x(i)},${y(r[key])}`).join(" ");
  return (
    <>
      <div className="legend">
        <span><i style={{ background: "var(--indigo)" }} />precision</span>
        <span><i style={{ background: "var(--teal)" }} />recall</span>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} width="100%" role="img"
           aria-label="Precision and recall across evaluation runs">
        {[0.5, 0.75, 1.0].map((g) => (
          <line key={g} x1={pad} x2={w - pad} y1={y(g)} y2={y(g)}
                stroke="var(--line)" strokeWidth="1" />
        ))}
        <path d={path("precision")} fill="none" stroke="var(--indigo)" strokeWidth="2.5" />
        <path d={path("recall")} fill="none" stroke="var(--teal)" strokeWidth="2.5" />
        {history.map((r, i) => (
          <g key={i}>
            <circle cx={x(i)} cy={y(r.precision)} r="3.5" fill="var(--indigo)" />
            <circle cx={x(i)} cy={y(r.recall)} r="3.5" fill="var(--teal)" />
          </g>
        ))}
      </svg>
    </>
  );
}

export default function CalibrationView({ engines }) {
  const [history, setHistory] = useState([]);
  const [engine, setEngine] = useState("ast");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    try { setHistory((await api.history()).history); }
    catch (e) { setError(e.message); }
  }
  useEffect(() => { load(); }, []);

  async function runEval() {
    setBusy(true); setError("");
    try { await api.runEval(engine, `manual run · ${engine}`); await load(); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  const latest = history[history.length - 1];

  return (
    <div className="view">
      <section className="panel">
        <p className="eyebrow">Calibration</p>
        <h2>How accurate is the scanner — measured, not asserted</h2>
        <p className="lede">
          Every sample carries its own ground truth. Findings are scored by
          exact (rule, line) match, so these numbers are arithmetic. Re-running
          after a change is how you catch a regression before it ships.
        </p>

        <div className="toolbar">
          <label className="field">
            engine
            <select value={engine} onChange={(e) => setEngine(e.target.value)}>
              {engines.map((eng) => (
                <option key={eng.name} value={eng.name} disabled={!eng.available}>
                  {eng.name}{eng.name === "llm" && !eng.available ? " (needs local Ollama)" : ""}
                </option>
              ))}
            </select>
          </label>
          <span className="grow" />
          <button className="btn btn-primary" onClick={runEval} disabled={busy}>
            {busy ? "Running…" : `Run eval · ${engine}`}
          </button>
        </div>
        {error && <div className="error-box">{error}</div>}

        {latest && (
          <>
            <div className="gauges">
              <RingGauge label="precision" value={latest.precision} color="var(--indigo)" />
              <RingGauge label="recall" value={latest.recall} color="var(--teal)" />
              <RingGauge label="f1" value={latest.f1} color="var(--violet)" />
            </div>
            <div className="confusion">
              <div className="tp"><b>{latest.tp}</b> true positives</div>
              <div className="fp"><b>{latest.fp}</b> false positives</div>
              <div className="fn"><b>{latest.fn}</b> missed</div>
              <div className="meta">{latest.engine} · {latest.samples} samples</div>
            </div>
          </>
        )}
      </section>

      {latest && (latest.false_positives.length > 0 || latest.false_negatives.length > 0) && (
        <section className="panel">
          <p className="eyebrow">Where it fails</p>
          <h2>The honest part — exactly what this engine gets wrong</h2>
          <div className="fails">
            {latest.false_positives.map((f, i) => (
              <div className="fail" key={`fp${i}`}>
                <span className="tag tag-fp">false pos</span>
                <span className="sample">{f.sample}:{f.line}</span>
                <span className="note">flagged {f.rule_id} on clean code</span>
              </div>
            ))}
            {latest.false_negatives.map((f, i) => (
              <div className="fail" key={`fn${i}`}>
                <span className="tag tag-fn">missed</span>
                <span className="sample">{f.sample}:{f.line}</span>
                <span className="note">did not catch {f.rule_id}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="panel">
        <p className="eyebrow">Regression history</p>
        <h2>Accuracy across runs</h2>
        <Trend history={history} />
        <div style={{ marginTop: 14 }}>
          {[...history].reverse().map((r, i) => (
            <div className="run-row" key={i}>
              <span className="note">{r.note || r.version}</span>
              <span className="num">P {pct(r.precision)}</span>
              <span className="num">R {pct(r.recall)}</span>
              <span className="num">F1 {pct(r.f1)}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
