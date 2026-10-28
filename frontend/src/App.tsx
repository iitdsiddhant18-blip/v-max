import { useEffect, useRef, useState } from "react";
import SamplePlayer, { ExportView } from "./SamplePlayer";
import { GeneratedExportView, LocalizedExportView, PreparedLessonView } from "./LessonPlayer";
import LandingHero from "./LandingHero";
import StudioPage from "./StudioPage";
import "./landing.css";

export default function App() {
  const path = window.location.pathname;

  // Protected Phase 1-4 pure render routes: must never load 3D or marketing elements
  if (path === "/render") return <ExportView />;
  if (path === "/render-lesson") return <GeneratedExportView />;
  if (path === "/render-localized") return <LocalizedExportView />;
  if (path === "/lesson") return <PreparedLessonView />;

  return <RouterMainApp initialRoute={path === "/studio" ? "studio" : "landing"} />;
}

function RouterMainApp({ initialRoute }: { initialRoute: "landing" | "studio" }) {
  const [route, setRoute] = useState<"landing" | "studio">(initialRoute);
  const [samplesOpen, setSamplesOpen] = useState(false);
  const samplePanelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Handle browser back and forward buttons
    const handlePopState = () => {
      const currentPath = window.location.pathname;
      setRoute(currentPath === "/studio" ? "studio" : "landing");
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function navigateTo(target: "landing" | "studio") {
    setRoute(target);
    const targetUrl = target === "studio" ? "/studio" : "/";
    if (window.location.pathname !== targetUrl) {
      window.history.pushState({}, "", targetUrl);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function pauseAllAudio() {
    document.querySelectorAll("audio").forEach((a) => a.pause());
  }

  function toggleSamples() {
    pauseAllAudio();
    setSamplesOpen((prev) => !prev);
  }

  return (
    <main className="blu-app-root">
      {route === "studio" ? (
        <StudioPage
          onBackHome={() => navigateTo("landing")}
          onPlaybackStart={pauseAllAudio}
        />
      ) : (
        <>
          <LandingHero
            onOpenStudio={() => navigateTo("studio")}
            onOpenSample={() => {
              setSamplesOpen(true);
              document.getElementById("samples")?.scrollIntoView({ behavior: "smooth" });
            }}
          />

          {/* ──────────────── Sample Lessons Section ──────────────── */}
          <section id="samples" className="blu-section" aria-label="Sample interactive lessons">
            <h2 className="blu-section-title">Explore Sample Visual Lessons</h2>
            <p className="blu-section-subtitle">
              Interactive demonstrations of speech-synchronized visual diagrams in English and Hindi.
            </p>

            <div style={{ textAlign: "center", marginBottom: 24 }}>
              <button
                type="button"
                className="blu-secondary-btn"
                aria-expanded={samplesOpen}
                onClick={toggleSamples}
                id="toggle-samples-btn"
              >
                <span>{samplesOpen ? "Hide Sample Player ▲" : "Launch Interactive Sample Player ▼"}</span>
              </button>
            </div>

            {samplesOpen && (
              <div
                ref={samplePanelRef}
                className="blu-studio-card"
                style={{ padding: 28 }}
              >
                <SamplePlayer />
              </div>
            )}
          </section>

          {/* ──────────────── Footer ──────────────── */}
          <footer
            style={{
              marginTop: 90,
              paddingTop: 32,
              borderTop: "1px solid var(--cream-border)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: 16,
              color: "var(--ink-500)",
              fontSize: 13.5,
            }}
          >
            <div>
              <strong>Blu Visual Teacher</strong> · Offline AI-Powered Animated Learning
            </div>
            <div>
              Developed by <strong>Team V-MAX</strong> for Hackathon Innovation
            </div>
          </footer>
        </>
      )}
    </main>
  );
}
