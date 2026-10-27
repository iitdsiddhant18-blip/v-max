import { useEffect, useRef, useState } from "react";
import SceneCanvas from "./SceneCanvas";
import type { ExportResult, Lesson, SampleTimeline } from "./types";

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

export default function LessonPlayer({ lesson, initialTimeline, onPlaybackStart }: {
  lesson: Lesson; initialTimeline?: SampleTimeline; onPlaybackStart?: () => void;
}) {
  const [timeline, setTimeline] = useState<SampleTimeline | null>(initialTimeline || null);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [working, setWorking] = useState<"prepare" | "export" | null>(null);
  const [video, setVideo] = useState<ExportResult | null>(null);
  const [error, setError] = useState("");
  const audio = useRef<HTMLAudioElement>(null);

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
    setVideo(null);
    setTime(0);
    setError("");
  }, [lesson, initialTimeline]);

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

  async function prepare() {
    takeAudioFocus();
    setWorking("prepare");
    setError("");
    setVideo(null);
    audio.current?.pause();
    setPlaying(false);
    setTimeline(null);
    try {
      const response = await fetch("/api/lesson/prepare", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lesson }),
      });
      setTimeline(await readJson<SampleTimeline>(response));
      setTime(0);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Narration failed");
    } finally {
      setWorking(null);
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
    setWorking("export");
    setError("");
    setVideo(null);
    try {
      setVideo(await readJson<ExportResult>(await fetch(
        `/api/lesson/export/${timeline.lesson_id}`, { method: "POST" })));
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
    <p className="text-sm text-neutral-600">English narration in Part 2b; Hindi/Kannada translation arrives in Part 3a.</p>
    <button className="mt-3 rounded bg-amber-400 px-4 py-2 disabled:opacity-50"
      disabled={working !== null} onClick={prepare}>
      {working === "prepare" ? "Preparing scene narration..." : "Prepare and preview lesson"}
    </button></>}
    {error && <p className="mt-3 text-red-700" role="alert">{error}</p>}
    {timeline && <div className="mt-4">
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
        <button className="rounded bg-blue-900 px-4 py-2 text-white" onClick={playPause}>
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
      <button className="mt-3 rounded bg-amber-400 px-4 py-2 disabled:opacity-50"
        disabled={working !== null} onClick={exportVideo}>
        {working === "export" ? "Exporting MP4..." : "Export this lesson as 720p MP4"}
      </button>
      {video && <a className="ml-3 text-blue-700 underline" href={video.video_url} download>
        Download {video.width}×{video.height} MP4</a>}
    </div>}
  </section>;
}
