import { useState } from "react";
import RobotMascot from "./RobotMascot";

interface LandingHeroProps {
  onOpenStudio: () => void;
  onOpenSample?: () => void;
}

export default function LandingHero({ onOpenStudio, onOpenSample }: LandingHeroProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <>
      {/* ──────────────── Top Navigation ──────────────── */}
      <header className="blu-topbar">
        <a className="blu-brand" href="#top">
          <span className="blu-brand-icon" aria-hidden="true">✦</span>
          <span>Blu Visual Teacher</span>
        </a>

        <nav aria-label="Main navigation" className={mobileMenuOpen ? "open" : ""}>
          <a href="#top" onClick={() => setMobileMenuOpen(false)}>Home</a>
          <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)}>How it works</a>
          <a href="#languages" onClick={() => setMobileMenuOpen(false)}>Languages</a>
          <a href="#samples" onClick={() => setMobileMenuOpen(false)}>Samples</a>
          <a href="#about" onClick={() => setMobileMenuOpen(false)}>About Blu</a>
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            type="button"
            className="blu-mobile-nav-toggle"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? "✕" : "☰"}
          </button>

          <button
            type="button"
            className="blu-topbar-action"
            onClick={onOpenStudio}
            id="topbar-open-studio"
          >
            Open Studio →
          </button>
        </div>
      </header>

      {/* ──────────────── Asymmetric Cream Hero ──────────────── */}
      <section className="blu-hero" id="top" aria-label="Blu Visual Teacher introduction">
        {/* Left Column: Heading, Subtext, CTAs, Capability Badges */}
        <div className="blu-hero-copy">
          <span className="blu-hero-sparkle" aria-hidden="true">✦</span>
          <h1>
            Turn Any Concept into an<br />
            <span className="blu-headline-accent">Animated Visual</span><br />
            Lesson
          </h1>
          <p>
            Local AI plans, animates and narrates step-by-step explanations in English,
            हिन्दी and ಕನ್ನಡ — 100% on your device, with no cloud APIs required.
          </p>

          <div className="blu-hero-cta-group">
            <button
              type="button"
              className="blu-primary-btn"
              onClick={onOpenStudio}
              id="hero-create-lesson-btn"
            >
              <span>Create a lesson</span>
              <span aria-hidden="true">↗</span>
            </button>

            {/* Hand-drawn golden curved arrow */}
            <svg
              className="blu-curved-arrow"
              viewBox="0 0 60 40"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                d="M 5 32 C 25 35, 42 22, 52 8"
                stroke="#d97706"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeDasharray="2 2"
              />
              <path
                d="M 44 6 L 53 7 L 50 16"
                stroke="#d97706"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>

            <a
              className="blu-secondary-btn"
              href="#samples"
              onClick={(e) => {
                if (onOpenSample) {
                  e.preventDefault();
                  onOpenSample();
                  document.getElementById("samples")?.scrollIntoView({ behavior: "smooth" });
                }
              }}
            >
              Watch a sample
            </a>
          </div>

          {/* Truthful capability badges replacing fake metrics */}
          <div className="blu-pill-metrics" aria-label="Platform capabilities">
            <div className="blu-pill-badge">
              <span className="dot" aria-hidden="true" />
              <span>3 Languages · English · हिन्दी · ಕನ್ನಡ</span>
            </div>
            <div className="blu-pill-badge">
              <span className="dot" aria-hidden="true" />
              <span>100% Offline AI · Local Qwen, Kokoro & Parler</span>
            </div>
            <div className="blu-pill-badge">
              <span className="dot" aria-hidden="true" />
              <span>30–90 Second Concept Lessons · MP4 & Subtitles</span>
            </div>
          </div>
        </div>

        {/* Right Column: 3D Robot, Orbital Rings, Floating Topic Chips */}
        <div className="blu-hero-art" aria-label="3D Blu robot mascot">
          {/* Soft golden backlight halo */}
          <div className="blu-hero-halo" aria-hidden="true" />

          {/* Hairline orbital rings */}
          <svg
            className="blu-orbit-svg"
            viewBox="0 0 500 500"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <ellipse
              cx="250"
              cy="250"
              rx="210"
              ry="110"
              transform="rotate(-20 250 250)"
              stroke="#e2caa2"
              strokeWidth="1.2"
              strokeDasharray="4 4"
            />
            <ellipse
              cx="250"
              cy="250"
              rx="230"
              ry="130"
              transform="rotate(28 250 250)"
              stroke="#ebd5b2"
              strokeWidth="1"
            />
          </svg>

          {/* Floating informative capability chips */}
          <span className="blu-float-chip blu-chip-1">◈ Animated Diagrams</span>
          <span className="blu-float-chip blu-chip-2">✦ Smart Learning</span>
          <span className="blu-float-chip blu-chip-3">✎ Step by Step</span>
          <span className="blu-float-chip blu-chip-4">▶ 720p MP4 Export</span>
          <span className="blu-float-chip blu-chip-5">🔒 100% Offline AI</span>
          <span className="blu-float-chip blu-chip-6">🌐 Multilingual Narration</span>

          {/* 3D Robot with hero-wide cursor head tracking */}
          <RobotMascot />
        </div>

        {/* Bottom Hero Bar: Get Started Here CTA + Sample Glass Card */}
        <div className="blu-hero-bottom-bar">
          <button
            type="button"
            className="blu-bottom-cta"
            onClick={onOpenStudio}
          >
            <span>Get Started Here</span>
            <span aria-hidden="true">→</span>
          </button>

          <div className="blu-sample-glass-card">
            <p>
              Explore how our visual engine transforms concepts into animated lessons.
              Start your learning journey today!
            </p>
            <button
              type="button"
              onClick={() => {
                if (onOpenSample) onOpenSample();
                document.getElementById("samples")?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              Watch Now
            </button>
          </div>
        </div>
      </section>

      {/* ──────────────── How Blu Works Section ──────────────── */}
      <section id="how-it-works" className="blu-section" aria-label="How Blu works">
        <h2 className="blu-section-title">How Blu Visual Teacher Works</h2>
        <p className="blu-section-subtitle">
          From concept to synchronized visual explanation in three local steps.
        </p>

        <div className="blu-how-grid">
          <div className="blu-how-card">
            <span className="blu-how-num">01</span>
            <h3>Enter Any Concept</h3>
            <p>
              Type any teachable concept in biology, physics, mathematics, chemistry,
              programming, or everyday processes.
            </p>
          </div>

          <div className="blu-how-card">
            <span className="blu-how-num">02</span>
            <h3>Local AI Planning</h3>
            <p>
              Our local Ollama model breaks the concept into structured scenes, teaching beats,
              and verified visual diagrams with zero cloud calls.
            </p>
          </div>

          <div className="blu-how-card">
            <span className="blu-how-num">03</span>
            <h3>Synchronized Voice & Video</h3>
            <p>
              Kokoro and Parler-TTS generate native speech in English, Hindi, or Kannada,
              driving animated visual highlights and 720p MP4 export.
            </p>
          </div>
        </div>
      </section>

      {/* ──────────────── Supported Languages Section ──────────────── */}
      <section id="languages" className="blu-section" aria-label="Supported languages">
        <h2 className="blu-section-title">Multilingual from the Core</h2>
        <p className="blu-section-subtitle">
          The same semantic lesson rendered identically with localized labels, native speech, and captions.
        </p>

        <div className="blu-lang-grid">
          <div className="blu-lang-card">
            <div className="blu-lang-script">English</div>
            <div className="blu-lang-name">Natural Narration</div>
            <p className="blu-lang-desc">
              Kokoro ONNX high-quality natural voice with millisecond speech-cue alignment.
            </p>
          </div>

          <div className="blu-lang-card">
            <div className="blu-lang-script">हिन्दी</div>
            <div className="blu-lang-name">Devanagari Script</div>
            <p className="blu-lang-desc">
              IndicTrans2 translation with glossary protection for formulas and Noto Sans Devanagari typography.
            </p>
          </div>

          <div className="blu-lang-card">
            <div className="blu-lang-script">ಕನ್ನಡ</div>
            <div className="blu-lang-name">Kannada Script</div>
            <p className="blu-lang-desc">
              Indic Parler-TTS dedicated synthesis with beautiful Noto Sans Kannada combining glyphs.
            </p>
          </div>
        </div>
      </section>

      {/* ──────────────── About Section ──────────────── */}
      <section id="about" className="blu-section" aria-label="About Team V-MAX and Blu">
        <h2 className="blu-section-title">Built for Accessible Learning</h2>
        <p className="blu-section-subtitle">
          Created by <strong>Team V-MAX</strong> for hackathon innovation. Designed to operate
          completely offline on standard consumer hardware (16GB RAM, RTX 3050 Laptop), ensuring
          privacy and education accessibility everywhere.
        </p>
      </section>
    </>
  );
}
