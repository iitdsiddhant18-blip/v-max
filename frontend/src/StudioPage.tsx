import { useEffect, useState } from "react";
import type { GenerateRequest, GenerateResponse, LanguageCode, Level } from "./types";
import LessonPlayer from "./LessonPlayer";

interface StudioPageProps {
  onBackHome: () => void;
  onPlaybackStart?: () => void;
}

const SAMPLE_PROMPTS = [
  "How does the small intestine absorb nutrients?",
  "Why is the graph of y = x squared a parabola?",
  "How does Tower of Hanoi work with 3 disks?",
  "Why does a heavier block accelerate less under the same force?",
  "How does the water cycle move water around Earth?",
];

export default function StudioPage({ onBackHome, onPlaybackStart }: StudioPageProps) {
  const [topic, setTopic] = useState("Why is the graph of y = x squared a parabola?");
  const [level, setLevel] = useState<Level>("beginner");
  const [language, setLanguage] = useState<LanguageCode>("en");
  const [seconds, setSeconds] = useState(0); // 0 = Auto
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [serverOnline, setServerOnline] = useState<boolean | null>(null);

  // Check local server connection status on mount
  useEffect(() => {
    let active = true;
    fetch("/api/lesson/sample")
      .then((res) => {
        if (active) setServerOnline(res.ok);
      })
      .catch(() => {
        if (active) setServerOnline(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleGenerate(e: React.SyntheticEvent) {
    e.preventDefault();
    const cleanTopic = topic.trim();
    if (!cleanTopic) {
      setError("Please enter an educational concept to explain.");
      return;
    }
    if (cleanTopic.length < 3) {
      setError("Topic is too short. Please enter a full question or concept.");
      return;
    }

    setBusy(true);
    setError(null);
    document.querySelectorAll("audio").forEach((audio) => audio.pause());

    const body: GenerateRequest = {
      topic: cleanTopic,
      level,
      language,
      target_seconds: seconds || 60,
      duration_mode: seconds === 0 ? "auto" : "manual",
    };

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Server returned ${res.status}`);
      }
      const data = (await res.json()) as GenerateResponse;
      setResult(data);
      // Smooth scroll down to player
      setTimeout(() => {
        document.getElementById("studio-player-anchor")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate lesson. Ensure local Ollama is running.");
    } finally {
      setBusy(false);
    }
  }

  function handleReset() {
    setResult(null);
    setError(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="blu-studio-container" id="studio">
      {/* ──────────────── Studio Header Bar ──────────────── */}
      <header className="blu-studio-header">
        <button
          type="button"
          onClick={onBackHome}
          className="blu-back-link"
          id="studio-back-home"
        >
          <span aria-hidden="true">←</span>
          <span>Back to Home</span>
        </button>

        <div className="blu-brand" style={{ fontSize: 20 }}>
          <span className="blu-brand-icon" style={{ width: 34, height: 34, fontSize: 15 }}>✦</span>
          <span>Blu Lesson Studio</span>
        </div>

        <div className={`blu-status-badge ${serverOnline === false ? "offline" : ""}`}>
          <span className="blu-status-dot" aria-hidden="true" />
          <span>
            {serverOnline === null
              ? "Checking local AI..."
              : serverOnline
              ? "Connected to local server"
              : "Local server offline"}
          </span>
        </div>
      </header>

      {/* ──────────────── Step A: Create Lesson Card ──────────────── */}
      <section className="blu-studio-card" aria-label="Create lesson form">
        <h2>What would you like to understand?</h2>
        <p className="blu-studio-subtitle">
          Type any concept in science, mathematics, coding, history, or everyday life.
        </p>

        {/* Quick Suggestion Chips */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 20 }}>
          {SAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => setTopic(prompt)}
              style={{
                background: topic === prompt ? "#fef08a" : "#fefce8",
                border: "1px solid #fde047",
                borderRadius: 9999,
                padding: "6px 14px",
                fontSize: 12.5,
                fontWeight: 650,
                color: "#713f12",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {prompt}
            </button>
          ))}
        </div>

        <form onSubmit={handleGenerate}>
          <div className="blu-form-group">
            <label className="blu-form-label" htmlFor="topic-input">
              Educational Concept or Question
            </label>
            <textarea
              id="topic-input"
              className="blu-textarea"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. How do lungs exchange oxygen and carbon dioxide?"
              disabled={busy}
              rows={3}
            />
          </div>

          <div className="blu-controls-grid">
            <div>
              <label className="blu-form-label" htmlFor="level-select">
                Learning Level
              </label>
              <select
                id="level-select"
                className="blu-select"
                value={level}
                onChange={(e) => setLevel(e.target.value as Level)}
                disabled={busy}
              >
                <option value="beginner">Beginner (Introductory)</option>
                <option value="intermediate">Intermediate (In-depth)</option>
              </select>
            </div>

            <div>
              <label className="blu-form-label" htmlFor="language-select">
                Narration Language
              </label>
              <select
                id="language-select"
                className="blu-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value as LanguageCode)}
                disabled={busy}
              >
                <option value="en">English (Kokoro ONNX)</option>
                <option value="hi">हिन्दी (Devanagari Script)</option>
                <option value="kn">ಕನ್ನಡ (Kannada Script)</option>
              </select>
            </div>

            <div>
              <label className="blu-form-label" htmlFor="duration-select">
                Lesson Duration
              </label>
              <select
                id="duration-select"
                className="blu-select"
                value={seconds}
                onChange={(e) => setSeconds(Number(e.target.value))}
                disabled={busy}
              >
                <option value={0}>Auto · concept complexity (30–90s)</option>
                <option value={30}>30 seconds (Concise)</option>
                <option value={60}>60 seconds (Standard)</option>
                <option value={90}>90 seconds (Comprehensive)</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            className="blu-studio-submit-btn"
            disabled={busy}
            id="studio-generate-btn"
          >
            {busy ? (
              <span>Planning lesson, drawing diagrams & synthesizing speech...</span>
            ) : (
              <span>Generate Visual Lesson →</span>
            )}
          </button>
        </form>

        {error && (
          <div
            role="alert"
            style={{
              marginTop: 20,
              padding: "16px 20px",
              background: "#fef2f2",
              border: "1px solid #fecaca",
              borderRadius: 16,
              color: "#991b1b",
              fontSize: 14,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>{error}</span>
            <button
              type="button"
              onClick={() => setError(null)}
              style={{
                background: "transparent",
                border: "none",
                fontWeight: "bold",
                color: "#991b1b",
                cursor: "pointer",
              }}
            >
              ✕
            </button>
          </div>
        )}
      </section>

      {/* ──────────────── Step B: Generated Lesson & Interactive Player ──────────────── */}
      {result && (
        <section
          id="studio-player-anchor"
          className="blu-studio-card"
          style={{ marginTop: 32 }}
          aria-label="Generated lesson player"
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
            <div>
              <span
                style={{
                  display: "inline-block",
                  padding: "4px 10px",
                  background: "#fefce8",
                  border: "1px solid #fde047",
                  borderRadius: 9999,
                  fontSize: 12,
                  fontWeight: 750,
                  color: "#854d0e",
                  marginBottom: 8,
                }}
              >
                {result.source === "llm" ? "✦ Local AI Structured Lesson" : "✦ Structured Concept Outline"}
              </span>
              <h2 style={{ fontSize: 26, margin: 0 }}>{result.lesson.title}</h2>
              <p style={{ margin: "4px 0 0", fontSize: 13.5, color: "#64748b" }}>
                Level: {result.request.level} · Requested Language: {result.request.language.toUpperCase()}
              </p>
            </div>

            <button
              type="button"
              onClick={handleReset}
              className="blu-secondary-btn"
              style={{ fontSize: 13, padding: "8px 18px" }}
            >
              ← Create Another Lesson
            </button>
          </div>

          <div style={{ marginTop: 24 }}>
            {result.source === "llm" ? (
              <LessonPlayer
                key={JSON.stringify(result.lesson)}
                lesson={result.lesson}
                targetLanguage={language}
                onPlaybackStart={onPlaybackStart}
              />
            ) : (
              <div
                role="alert"
                style={{
                  padding: 20,
                  background: "#fffbeb",
                  border: "1px solid #fef08a",
                  borderRadius: 16,
                  color: "#92400e",
                }}
              >
                <p style={{ margin: 0, fontWeight: 700 }}>Concept Outline Created</p>
                <p style={{ margin: "6px 0 0", fontSize: 14 }}>
                  The local planner produced an outline. Ensure Ollama is loaded with Qwen3:4b for full
                  multilingual speech synthesis and 720p MP4 export.
                </p>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
