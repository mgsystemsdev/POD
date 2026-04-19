import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <nav className="border-b border-slate-800 px-4 py-3 text-sm">
        <Link to="/" className="text-indigo-400 hover:text-indigo-300">
          Home
        </Link>
      </nav>
      <main className="p-4">
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </main>
    </div>
  );
}

function Home() {
  const [status, setStatus] = useState<string>("loading…");
  const [projects, setProjects] = useState<unknown[] | null>(null);

  useEffect(() => {
    fetch("/api/projects")
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
      })
      .then((data) => {
        setProjects(Array.isArray(data) ? data : []);
        setStatus("ok");
      })
      .catch((e: Error) => setStatus(`error: ${e.message}`));
  }, []);

  return (
    <div className="space-y-2">
      <h1 className="text-lg font-medium text-slate-100">Execution dashboard</h1>
      <p className="text-sm text-slate-400">
        Proxy: <code className="text-slate-300">/api/*</code> →{" "}
        <code className="text-slate-300">127.0.0.1:8765</code>
      </p>
      <p className="text-sm">
        <span className="text-slate-500">GET /api/projects:</span>{" "}
        <span className="text-slate-300">{status}</span>
      </p>
      {projects && (
        <pre className="overflow-auto rounded border border-slate-800 bg-slate-900 p-3 text-xs text-slate-400">
          {JSON.stringify(projects, null, 2)}
        </pre>
      )}
    </div>
  );
}
