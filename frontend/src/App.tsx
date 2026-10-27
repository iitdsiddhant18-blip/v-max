import { useState } from "react";
import type { GenerateRequest, GenerateResponse, LanguageCode, Level } from "./types";
import SamplePlayer, { ExportView } from "./SamplePlayer";

export default function App() {
  if (window.location.pathname === "/render") return <ExportView />;
  return <MainApp />;
}

function MainApp() {
  const [topic, setTopic] = useState("How does a Python loop work?");
  const [level, setLevel] = useState<Level>("beginner");
  const [language, setLanguage] = useState<LanguageCode>("en");
  const [seconds, setSeconds] = useState(60);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.SyntheticEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const body: GenerateRequest = { topic, level, language, target_seconds: seconds };
    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      setResult((await res.json()) as GenerateResponse);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl p-6 font-sans">
      <h1 className="text-3xl font-bold">Blu Visual Teacher</h1>
      <p className="mt-1 text-sm text-neutral-600">Phase 1a form + Part 1b narrated sample.</p>

      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <label className="block">
          <span className="text-sm font-medium">Topic</span>
          <input
            className="mt-1 w-full rounded border p-2"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
        </label>
        <div className="grid grid-cols-3 gap-3">
          <label className="block">
            <span className="text-sm font-medium">Level</span>
            <select
              className="mt-1 w-full rounded border p-2"
              value={level}
              onChange={(e) => setLevel(e.target.value as Level)}
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-medium">Language</span>
            <select
              className="mt-1 w-full rounded border p-2"
              value={language}
              onChange={(e) => setLanguage(e.target.value as LanguageCode)}
            >
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
              <option value="kn">ಕನ್ನಡ</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-medium">Length</span>
            <select
              className="mt-1 w-full rounded border p-2"
              value={seconds}
              onChange={(e) => setSeconds(Number(e.target.value))}
            >
              <option value={30}>30 s</option>
              <option value={60}>60 s</option>
              <option value={90}>90 s</option>
            </select>
          </label>
        </div>
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-amber-400 px-5 py-2 font-medium disabled:opacity-50"
        >
          {busy ? "Working..." : "Create lesson"}
        </button>
      </form>

      {error && (
        <p role="alert" className="mt-4 rounded bg-red-100 p-3 text-red-800">
          {error}
        </p>
      )}

      {result && (
        <section className="mt-6" data-testid="result">
          <h2 className="text-xl font-bold">{result.lesson.title}</h2>
          <p className="text-sm text-neutral-600">
            source: {result.source} | requested language: {result.request.language}
          </p>
          <ol className="mt-3 list-decimal space-y-2 pl-5">
            {result.lesson.scenes.map((s, i) => (
              <li key={i}>
                <span className="font-medium">{s.heading}</span>{" "}
                <span className="text-xs text-neutral-500">({s.type})</span>
                <div className="text-sm text-neutral-700">{s.narration}</div>
              </li>
            ))}
          </ol>
        </section>
      )}
      <SamplePlayer />
    </main>
  );
}
