import { useEffect, useState } from "react";
import { api } from "./api.js";
import ScanView from "./components/ScanView.jsx";
import CalibrationView from "./components/CalibrationView.jsx";

export default function App() {
  const [tab, setTab] = useState("scan");
  const [engines, setEngines] = useState([{ name: "ast", available: true }]);
  const [online, setOnline] = useState(false);

  useEffect(() => {
    api.engines()
      .then((res) => { setEngines(res.engines); setOnline(true); })
      .catch(() => setOnline(false));
  }, []);

  return (
    <div className="wrap">
      <header className="masthead">
        <span className="statusline">
          <span className="pulse" style={{ background: online ? "var(--green)" : "var(--amber)" }} />
          {online ? "backend connected" : "connecting to backend…"}
        </span>
        <div className="brand">
          <h1>Litmus<span className="dot">.</span></h1>
          <span className="tagline">measured python security scanning</span>
        </div>
        <p className="subline">
          A static scanner for a fixed set of Python security mistakes that
          <strong> reports its own precision and recall</strong> on a labeled
          dataset, instead of asking you to trust it. The AST engine is measured
          head-to-head against a naive regex baseline.
        </p>
        <div className="tabs" role="tablist">
          <button className="tab" role="tab" aria-selected={tab === "scan"}
                  onClick={() => setTab("scan")}>scan</button>
          <button className="tab" role="tab" aria-selected={tab === "calibration"}
                  onClick={() => setTab("calibration")}>calibration</button>
        </div>
      </header>

      <main>
        {tab === "scan"
          ? <ScanView engines={engines} />
          : <CalibrationView engines={engines} />}
      </main>

      <footer className="foot">
        {}
      </footer>
    </div>
  );
}
