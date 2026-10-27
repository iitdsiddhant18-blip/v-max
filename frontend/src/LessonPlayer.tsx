import { useEffect, useRef, useState } from "react";
import SceneCanvas from "./SceneCanvas";
import type { ExportResult, GeneratedLanguage, Lesson, SampleTimeline } from "./types";

async function readJson<T>(response: Response): Promise<T> {
  const value = await response.json();
  if (!response.ok) throw new Error(value.detail || `HTTP ${response.status}`);
  return value as T;
}

export function GeneratedExportView() {
  const identifier = new URLSearchParams(window.location.search).get("id") || "";
  const [timeline, setTimeline] = useState<SampleTimeline | null>(null);
  const [time, setTime] = useState(0);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    window.__BLU_READY__ = false;
    window.__BLU_SET_TIME__ = (seconds: number) => setTime(seconds);
    fetch(`/api/lesson/timeline/${identifier}`)
      .then(readJson<SampleTimeline>)
      .then(async data => {
        if (!active) return;
        setTimeline(data);
        await document.fonts.ready;
        requestAnimationFrame(() => { if (active) window.__BLU_READY__ = true; });
      })
      .catch(reason => { if (active) setError(String(reason)); });
    return () => {
      active = false;
      window.__BLU_READY__ = false;
      delete window.__BLU_SET_TIME__;
    };
  }, [identifier]);
  return <div style={{ width: 1280, height: 720, margin: 0, overflow: "hidden" }}>
    {timeline ? <SceneCanvas timeline={timeline} time={time} /> : <div>{error || "Loading..."}</div>}
  </div>;
}

export function LocalizedExportView() {
  const identifier = new URLSearchParams(window.location.search).get("id") || "";
  const [timeline, setTimeline] = useState<SampleTimeline | null>(null);
  const [time, setTime] = useState(0);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    window.__BLU_READY__ = false;
    window.__BLU_SET_TIME__ = (seconds: number) => setTime(seconds);
    fetch(`/api/localized/timeline/${identifier}`)
      .then(readJson<SampleTimeline>)
      .then(async data => {
        if (!active) return;
        setTimeline(data);
        await document.fonts.ready;
        requestAnimationFrame(() => { if (active) window.__BLU_READY__ = true; });
      })
      .catch(reason => { if (active) setError(String(reason)); });
    return () => {
      active = false;
      window.__BLU_READY__ = false;
      delete window.__BLU_SET_TIME__;
    };
  }, [identifier]);
  return <div style={{ width: 1280, height: 720, margin: 0, overflow: "hidden" }}>
    {timeline ? <SceneCanvas timeline={timeline} time={time} /> : <div>{error || "Loading localized lesson..."}</div>}
  </div>;
}

export function PreparedLessonView() {
  const identifier = new URLSearchParams(window.location.search).get("id") || "";
  const [prepared, setPrepared] = useState<SampleTimeline | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    fetch(`/api/lesson/timeline/${encodeURIComponent(identifier)}`)
      .then(readJson<SampleTimeline>)
      .then(data => { if (active) setPrepared(data); })
      .catch(reason => { if (active) setError(String(reason)); });
    return () => { active = false; };
  }, [identifier]);
  return <main className="mx-auto max-w-4xl p-6 font-sans">
    <a href="/" className="text-blue-700 underline">Create another lesson</a>
    {prepared ? <>
      <h1 className="mt-4 text-3xl font-bold">{prepared.lesson.title}</h1>
      <p className="mt-2 text-neutral-600">Prepared English lesson · {prepared.total_seconds.toFixed(1)} seconds</p>
      <LessonPlayer lesson={prepared.lesson} initialTimeline={prepared} />
    </> : <p role={error ? "alert" : undefined}>{error || "Loading prepared lesson..."}</p>}
  </main>;
}

export default function LessonPlayer({ lesson, initialTimeline, targetLanguage = "en", onPlaybackStart }: {
  lesson: Lesson; initialTimeline?: SampleTimeline; targetLanguage?: GeneratedLanguage; onPlaybackStart?: () => void;
}) {
  const [currentLang, setCurrentLang] = useState<GeneratedLanguage>(
    (initialTimeline?.language as GeneratedLanguage) || targetLanguage || "en"
  );
  const [sourceLessonId, setSourceLessonId] = useState<string | null>(
    initialTimeline?.source_lesson_id || (initialTimeline?.language === "en" ? initialTimeline.lesson_id || null : null)
  );
  const [timeline, setTimeline] = useState<SampleTimeline | null>(initialTimeline || null);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [working, setWorking] = useState<string | null>(null);
  const [video, setVideo] = useState<ExportResult | null>(null);
  const [error, setError] = useState("");
  const audio = useRef<HTMLAudioElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  function takeAudioFocus() {
    onPlaybackStart?.();
    document.querySelectorAll("audio").forEach(other => {
      if (other !== audio.current) other.pause();
    });
  }

  // Keep the actual element for cleanup: React clears refs during unmount.
  useEffect(() => {
    const element = audio.current;
    return () => element?.pause();
  }, [timeline]);

  // A newly generated lesson must never reuse a previous topic's timeline.
  useEffect(() => {
    audio.current?.pause();
    setPlaying(false);
    setTimeline(initialTimeline || null);
    setCurrentLang((initialTimeline?.language as GeneratedLanguage) || targetLanguage || "en");
    setSourceLessonId(initialTimeline?.source_lesson_id || (initialTimeline?.language === "en" ? initialTimeline.lesson_id || null : null));
    setVideo(null);
    setTime(0);
    setError("");
  }, [lesson, initialTimeline, targetLanguage]);

  useEffect(() => {
    if (!playing) return;
    let frame = 0;
    const tick = () => {
      if (audio.current) setTime(audio.current.currentTime);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [playing]);

  async function prepareForLanguage(lang: GeneratedLanguage) {
    takeAudioFocus();
    abortControllerRef.current?.abort();
    const abortCtrl = new AbortController();
    abortControllerRef.current = abortCtrl;

    audio.current?.pause();
    setPlaying(false);
    setError("");
    setVideo(null);
    setTimeline(null);

    try {
      if (lang === "en") {
        setWorking("Preparing English narration...");
        const response = await fetch("/api/lesson/prepare", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ lesson }),
          signal: abortCtrl.signal,
        });
        const data = await readJson<SampleTimeline>(response);
        if (abortCtrl.signal.aborted) return;
        setTimeline(data);
        setSourceLessonId(data.lesson_id || null);
        setCurrentLang("en");
        setTime(0);
      } else {
        // Hindi or Kannada: needs English source ID first
        let srcId = sourceLessonId;
        if (!srcId) {
          setWorking("Preparing English source foundation...");
          const engRes = await fetch("/api/lesson/prepare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lesson }),
            signal: abortCtrl.signal,
          });
          const engData = await readJson<SampleTimeline>(engRes);
          if (abortCtrl.signal.aborted) return;
          srcId = engData.lesson_id || null;
          setSourceLessonId(srcId);
        }

        if (!srcId) throw new Error("Could not obtain source lesson ID");

        const statusText = lang === "hi"
          ? "Translating and preparing Hindi voice (Kokoro hf_alpha)..."
          : "Translating and preparing Kannada voice (ai4bharat/indic-parler-tts)...";
        setWorking(statusText);

        const response = await fetch("/api/localized/prepare", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ source_lesson_id: srcId, language: lang }),
          signal: abortCtrl.signal,
        });
        const data = await readJson<SampleTimeline>(response);
        if (abortCtrl.signal.aborted) return;
        setTimeline(data);
        setCurrentLang(lang);
        setTime(0);
      }
    } catch (reason) {
      if (abortCtrl.signal.aborted) return;
      setError(reason instanceof Error ? reason.message : "Preparation failed");
    } finally {
      if (!abortCtrl.signal.aborted) {
        setWorking(null);
      }
    }
  }

  function seek(value: number) {
    if (!timeline || !audio.current) return;
    const bounded = Math.max(0, Math.min(timeline.total_seconds, value));
    audio.current.currentTime = bounded;
    setTime(bounded);
  }

  async function playPause() {
    if (!audio.current) return;
    if (!audio.current.paused) {
      audio.current.pause();
      setPlaying(false);
    } else {
      try {
        takeAudioFocus();
        await audio.current.play();
        setPlaying(true);
      } catch (reason) {
        setError(String(reason));
      }
    }
  }

  async function replay() {
    takeAudioFocus();
    seek(0);
    try {
      await audio.current?.play();
      setPlaying(true);
    } catch (reason) {
      setError(String(reason));
    }
  }

  async function exportVideo() {
    if (!timeline?.lesson_id) return;
    setWorking("Rendering 720p H.264/AAC MP4 video with FFmpeg...");
    setError("");
    setVideo(null);
    try {
      const endpoint = timeline.language === "en"
        ? `/api/lesson/export/${timeline.lesson_id}`
        : `/api/localized/export/${timeline.lesson_id}`;
      const res = await fetch(endpoint, { method: "POST" });
      setVideo(await readJson<ExportResult>(res));
    } catch (reason) {
      setError(String(reason));
    } finally {
      setWorking(null);
    }
  }

  const currentIndex = timeline ? timeline.scenes.reduce((index, scene, i) =>
    time >= scene.start_seconds ? i : index, 0) : 0;
  const currentEntry = timeline?.scenes[currentIndex];
  const currentScene = timeline?.lesson.scenes[currentIndex];
  const localTime = time - (currentEntry?.start_seconds || 0);
  const currentCue = currentEntry?.cues?.find(c => localTime >= c.start_seconds && localTime < c.end_seconds)
    || currentEntry?.cues?.[currentEntry.cues.length - 1];

  return <section className="mt-6 rounded-xl border p-4" aria-label="Generated lesson player">
    {!initialTimeline && <><h3 className="text-xl font-bold">Your generated lesson</h3>
    <p className="text-sm text-neutral-600">Plan once in English, then play and export in English, Hindi, or Kannada.</p>

    <div className="mt-3 flex items-center gap-2">
      <span className="text-sm font-medium">Select delivery language:</span>
      {(["en", "hi", "kn"] as GeneratedLanguage[]).map(lang => (
        <button
          key={lang}
          type="button"
          onClick={() => prepareForLanguage(lang)}
          disabled={working !== null}
          className={`rounded px-3 py-1 text-sm font-medium border ${
            currentLang === lang ? "bg-blue-900 text-white border-blue-900" : "bg-white text-neutral-800 hover:bg-neutral-100"
          } disabled:opacity-50`}
        >
          {lang === "en" ? "English" : lang === "hi" ? "हिन्दी" : "ಕನ್ನಡ"}
        </button>
      ))}
    </div>

    {!timeline && <button className="mt-3 rounded bg-amber-400 px-4 py-2 font-medium disabled:opacity-50"
      disabled={working !== null} onClick={() => prepareForLanguage(currentLang)}>
      {working || "Prepare and preview lesson"}
    </button>}</>}

    {working && <div className="mt-3 rounded bg-blue-50 p-3 text-blue-900 text-sm font-medium flex items-center gap-2">
      <span className="inline-block animate-spin">⟳</span>
      <span>{working}</span>
    </div>}

    {error && <p className="mt-3 text-red-700" role="alert">{error}</p>}

    {timeline && <div className="mt-4">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Language:</span>
          {(["en", "hi", "kn"] as GeneratedLanguage[]).map(lang => (
            <button
              key={lang}
              type="button"
              onClick={() => prepareForLanguage(lang)}
              disabled={working !== null}
              className={`rounded px-2.5 py-0.5 text-xs font-medium border ${
                timeline.language === lang ? "bg-blue-900 text-white border-blue-900" : "bg-white text-neutral-700 hover:bg-neutral-100"
              } disabled:opacity-50`}
            >
              {lang === "en" ? "English" : lang === "hi" ? "हिन्दी" : "ಕನ್ನಡ"}
            </button>
          ))}
        </div>
        <span className="text-xs text-neutral-500">Voice: {timeline.voice}</span>
      </div>

      <div className="overflow-hidden rounded-xl"><SceneCanvas timeline={timeline} time={time} /></div>

      {currentScene && <div className="mt-3 md:hidden">
        <p className="font-semibold">{currentScene.heading}</p>
        <p className="mt-1 text-base leading-relaxed" data-live-caption="true">
          {currentCue?.label && <strong className="mr-2">{currentCue.label}:</strong>}
          {currentCue?.text || currentScene.narration}</p>
        <details className="mt-2 text-sm">
          <summary className="cursor-pointer text-blue-800">Read scene details</summary>
          {currentScene.code && <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded bg-slate-100 p-3">
            {currentScene.code}</pre>}
          {currentScene.items.length > 0 && <ul className="mt-2 list-disc pl-5">
            {currentScene.items.map((item, i) => {
              const [label, fact] = item.split(" :: ");
              return <li key={i}><strong>{label}</strong>{fact ? `: ${fact}` : ""}</li>;
            })}</ul>}
        </details>
      </div>}

      <audio ref={audio} src={timeline.audio_url} preload="auto"
        onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)}
        onTimeUpdate={e => setTime(e.currentTarget.currentTime)}
        onEnded={() => { setPlaying(false); setTime(timeline.total_seconds); }} />

      <div className="mt-3 flex flex-wrap items-center gap-3">
        {timeline.lesson_id && window.location.pathname !== "/lesson" && <a
          className="text-blue-700 underline" href={`/lesson?id=${timeline.lesson_id}`}>
          Open larger player</a>}
        <button className="rounded bg-blue-900 px-4 py-2 text-white font-medium" onClick={playPause}>
          {playing ? "Pause" : "Play"}</button>
        <button className="rounded border px-3 py-2" onClick={() => {
          const next = timeline.scenes.find(s => s.start_seconds > time + 0.001);
          if (next) seek(next.start_seconds);
        }}>Next scene</button>
        <button className="rounded border px-3 py-2" onClick={replay}>Replay</button>
        <span>{time.toFixed(1)} / {timeline.total_seconds.toFixed(1)} s</span>
      </div>

      <input className="mt-3 w-full" type="range" min={0} max={timeline.total_seconds}
        step={0.05} value={time} onChange={e => seek(Number(e.target.value))}
        aria-label="Lesson progress" />

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <button className="rounded bg-amber-400 px-4 py-2 font-medium disabled:opacity-50"
          disabled={working !== null} onClick={exportVideo}>
          {working?.startsWith("Rendering") ? "Exporting MP4..." : "Export this lesson as 720p MP4"}
        </button>

        {timeline.subtitle_url && (
          <a className="text-blue-700 underline font-medium" href={timeline.subtitle_url} download>
            Download Subtitles (.srt)
          </a>
        )}

        {video && <a className="text-blue-700 underline font-medium" href={video.video_url} download>
          Download {video.width}×{video.height} MP4
        </a>}
      </div>
    </div>}
  </section>;
}
