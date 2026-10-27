import { useEffect, useRef, useState } from "react";
import SceneCanvas from "./SceneCanvas";
import type { ExportResult, SampleLanguage, SampleTimeline } from "./types";

declare global {
  interface Window {
    __BLU_READY__?: boolean;
    __BLU_SET_TIME__?: (seconds: number) => void;
  }
}

async function readJson<T>(response: Response): Promise<T> {
  const value = await response.json();
  if (!response.ok) throw new Error(value.detail || `HTTP ${response.status}`);
  return value as T;
}

// This route is used ONLY by headless Playwright. No clock, CSS animation, or audio playback.
export function ExportView() {
  const lang = new URLSearchParams(window.location.search).get("lang");
  const language: SampleLanguage = lang === "hi" ? "hi" : "en";
  const [timeline, setTimeline] = useState<SampleTimeline | null>(null);
  const [time, setTime] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    window.__BLU_READY__ = false;
    window.__BLU_SET_TIME__ = (seconds) => setTime(seconds);
    fetch(`/api/sample/timeline/${language}`)
      .then(readJson<SampleTimeline>)
      .then(async (data) => {
        if (!active) return;
        setTimeline(data);
        await document.fonts.ready;
        requestAnimationFrame(() => {
          if (active) window.__BLU_READY__ = true;
        });
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "Timeline load failed");
      });
    return () => {
      active = false;
      window.__BLU_READY__ = false;
      delete window.__BLU_SET_TIME__;
    };
  }, [language]);

  return (
    <div style={{ margin: 0, padding: 0, width: 1280, height: 720, overflow: "hidden" }}>
      {timeline ? <SceneCanvas timeline={timeline} time={time} /> : <div>{error || "Loading timeline..."}</div>}
    </div>
  );
}

export default function SamplePlayer() {
  const [language, setLanguage] = useState<SampleLanguage>("en");
  const [timeline, setTimeline] = useState<SampleTimeline | null>(null);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [working, setWorking] = useState<"prepare" | "export" | null>(null);
  const [video, setVideo] = useState<ExportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (!playing) return;
    let frame = 0;
    const update = () => {
      if (audioRef.current) setTime(audioRef.current.currentTime);
      frame = requestAnimationFrame(update);
    };
    frame = requestAnimationFrame(update);
    return () => cancelAnimationFrame(frame);
  }, [playing]);

  async function prepare() {
    setError(null);
    setWorking("prepare");
    setPlaying(false);
    setTimeline(null);
    setVideo(null);
    setTime(0);
    try {
      const response = await fetch("/api/sample/prepare", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language }),
      });
      setTimeline(await readJson<SampleTimeline>(response));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Audio preparation failed");
    } finally {
      setWorking(null);
    }
  }

  async function playPause() {
    const audio = audioRef.current;
    if (!audio) return;
    if (!audio.paused) {
      audio.pause();
      setPlaying(false);
    } else {
      try {
        await audio.play();
        setPlaying(true);
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Cannot play audio");
      }
    }
  }

  function seek(seconds: number) {
    if (!timeline || !audioRef.current) return;
    const bounded = Math.max(0, Math.min(timeline.total_seconds, seconds));
    audioRef.current.currentTime = bounded;
    setTime(bounded);
  }

  function nextScene() {
    if (!timeline) return;
    const next = timeline.scenes.find((scene) => scene.start_seconds > time + 0.001);
    if (next) seek(next.start_seconds);
  }

  async function replay() {
    seek(0);
    try {
      await audioRef.current?.play();
      setPlaying(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Cannot replay audio");
    }
  }

  async function exportVideo() {
    if (!timeline) return;
    setWorking("export");
    setError(null);
    setVideo(null);
    try {
      const response = await fetch("/api/sample/export", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language: timeline.language }),
      });
      setVideo(await readJson<ExportResult>(response));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "MP4 export failed");
    } finally {
      setWorking(null);
    }
  }

  return (
    <section className="mt-10 border-t pt-7" aria-label="Part 1b sample player">
      <h2 className="text-2xl font-bold">Part 1b: Narrated sample lesson</h2>
      <p className="mt-2 text-sm text-neutral-600">
        This is the fixed Python-loop sample. The topic form above still uses the Part 1a fallback.
        English and Hindi voices work here; Kannada and automatic translation come in Part 3a.
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <label htmlFor="sample-language">Voice:</label>
        <select id="sample-language" className="rounded border p-2" disabled={working !== null}
          value={language} onChange={(event) => {
            audioRef.current?.pause();
            setPlaying(false);
            setLanguage(event.target.value as SampleLanguage);
            setTimeline(null);
            setVideo(null);
            setTime(0);
          }}>
          <option value="en">English (hm_omega)</option>
          <option value="hi">हिन्दी (hf_alpha)</option>
        </select>
        <button className="rounded bg-amber-400 px-4 py-2 font-medium" disabled={working !== null}
          onClick={prepare}>{working === "prepare" ? "Generating audio..." : "Prepare sample voice"}</button>
      </div>
      {error && <p role="alert" className="mt-3 rounded bg-red-100 p-3 text-red-800">{error}</p>}
      {timeline && (
        <div className="mt-5">
          <div className="overflow-hidden rounded-xl border bg-slate-900">
            <SceneCanvas timeline={timeline} time={time} />
          </div>
          <audio ref={audioRef} src={timeline.audio_url} preload="auto"
            onTimeUpdate={(event) => setTime(event.currentTarget.currentTime)}
            onEnded={() => { setPlaying(false); setTime(timeline.total_seconds); }} />
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <button onClick={playPause} className="rounded bg-blue-900 px-4 py-2 text-white">
              {playing ? "Pause" : "Play"}
            </button>
            <button onClick={nextScene} className="rounded border px-4 py-2">Next scene</button>
            <button onClick={replay} className="rounded border px-4 py-2">Replay</button>
            <span className="text-sm tabular-nums">{time.toFixed(1)} / {timeline.total_seconds.toFixed(1)} s</span>
          </div>
          <input type="range" min={0} max={timeline.total_seconds} step={0.05} value={time}
            onChange={(event) => seek(Number(event.target.value))} aria-label="Lesson progress"
            className="mt-3 w-full" />
          <div className="mt-4 flex items-center gap-4">
            <button disabled={working !== null} onClick={exportVideo}
              className="rounded bg-amber-400 px-4 py-2 font-medium disabled:opacity-50">
              {working === "export" ? "Exporting MP4 (please wait)..." : "Export 720p MP4"}
            </button>
            {video && <a href={video.video_url} download className="text-blue-700 underline">
              Download MP4 ({video.width}×{video.height}, {video.video_codec}/{video.audio_codec})
            </a>}
          </div>
        </div>
      )}
    </section>
  );
}
