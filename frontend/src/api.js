// Thin wrapper over the backend. Every call returns parsed JSON or throws
// with the server's error detail so the UI can show something specific.
async function call(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  analyze: (code, engine) =>
    call("/api/analyze", {
      method: "POST",
      body: JSON.stringify({ code, engine }),
    }),
  engines: () => call("/api/engines"),
  rules: () => call("/api/rules"),
  runEval: (engine, note) =>
    call("/api/eval/run", {
      method: "POST",
      body: JSON.stringify({ engine, note }),
    }),
  history: () => call("/api/eval/history"),
};
