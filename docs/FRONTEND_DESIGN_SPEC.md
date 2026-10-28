# Frontend Design Specification: Blu Visual Teacher

Reference Inspiration: Cream-colored educational technology landing page ("Nowledge" reference).
Brand Identity: Blu Visual Teacher (Team V-MAX).
Architecture: Offline-first React 19 + TypeScript + Vite + Tailwind/Vanilla CSS + Three.js / React Three Fiber.

---

## 1. Reference Decomposition & Truthful Adaptation

| Reference Element | Original Visual Style | Blu Truthful Adaptation | Component / Location |
|---|---|---|---|
| **Brand Wordmark** | Black text with yellow hexagon mark "Nowledge" | "Blu Visual Teacher" with custom gold hexagon + spark icon | `LandingHero.tsx` / `StudioPage.tsx` |
| **Header Nav** | Horizontal links: Home, About, Features, Pricing, Support | "Home", "How it Works", "Languages", "Samples", "About Blu" | Top bar `<nav>` |
| **Top Action** | Rounded outlined pill "Contact Us" | "Open Studio" pill button linking to `/studio` | Top bar CTA |
| **Main Headline** | Oversized 3-line bold black geometric heading | "Turn Any Concept into an Animated Visual Lesson" | Hero Left column `<h1>` |
| **Subtext** | 2-line explanation | "Local AI plans, animates and narrates step-by-step explanations in English, हिन्दी and ಕನ್ನಡ — 100% on your device." | Hero Left subtext |
| **Primary CTA** | Warm yellow pill button "Explore More" + curved arrow | Warm yellow pill button "Create a lesson" / "Open Studio" + curved golden arrow | Hero Left CTA |
| **Secondary CTA** | N/A | "Watch a sample" secondary outlined pill button | Hero Left CTA |
| **Metrics Badges** | Fake user stats (175K users, 7M users, 108+ classes) | Replaced with truthful capabilities: "3 Languages (EN · HI · KN)", "100% Offline AI", "30–90s Animated Lessons" | Hero Left bottom pills |
| **Hero Mascot** | Large 3D yellow robot standing on books, holding books, big expressive eyes, blue ear-cups, antenna | Original 3D Blu mascot in Three.js/R3F with independent head pivot, glossy dark visor, expressive tracking eyes, antenna, blue ear-cups, holding stacked books | `RobotMascot.tsx` |
| **Orbital Rings & Chips** | Delicate golden hairline orbits with floating topic chips | Golden SVG/CSS hairline orbital loops with chips: "Animated Diagrams", "Offline AI", "English · हिन्दी · ಕನ್ನಡ", "720p MP4", "Deterministic Motion" | Hero Right `blu-hero-art` |
| **Bottom Center CTA** | Pill button "Get Started Here" | "Get Started Here" linking directly to `/studio` | Hero Bottom Center |
| **Bottom Right Glass Card**| Mini preview card with "Watch Now" | Real sample preview glass card: "Explore how our visual engine transforms concepts into animated lessons" + "Watch Now" | Hero Bottom Right |

---

## 2. Color Palette & Design Tokens

```css
:root {
  --cream-bg: #fbf7ee;
  --cream-surface: #ffffff;
  --cream-card: #fefbf2;
  --cream-border: #eadfca;
  --cream-border-subtle: #f2e9d7;
  
  --ink-primary: #121826;
  --ink-secondary: #4b5565;
  --ink-muted: #737d8c;
  
  --yellow-primary: #f6c63c;
  --yellow-hover: #e5b329;
  --yellow-glow: rgba(246, 198, 60, 0.35);
  
  --gold-accent: #d89614;
  --blue-accent: #58b6e6;
  --blue-earcup: #4aa3db;
  
  --radius-pill: 9999px;
  --radius-card: 28px;
  --radius-control: 14px;
}
```

---

## 3. Two Connected Spaces Architecture

```
                       ┌─────────────────────────┐
                       │       App.tsx           │
                       │  Client-side routing    │
                       └────────────┬────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
      Path = "/"              Path = "/studio"          Path = "/render*"
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   LandingHero    │      │    StudioPage    │      │  Pure Renderers  │
│  Reference Hero  │◄────►│  Step 1: Create  │      │  LessonPlayer /  │
│ 3D Robot Mascot  │      │  Step 2: Player  │      │  SceneCanvas     │
│ How it Works     │      │  MP4/SRT Export  │      │ (No 3D / Mascot) │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## 4. 3D Robot Head-Tracking Contract

- **Head Yaw (Horizontal)**: $\pm 0.40 \text{ rad}$, clamped. Left cursor turns head left; right cursor turns head right.
- **Head Pitch (Vertical)**: $\pm 0.22 \text{ rad}$, clamped. Upward cursor tilts head up; downward cursor tilts head down.
- **Head Pivot vs Body**: Only the head group rotates. Torso, feet, and books remain anchored in space.
- **Pupil Tracking**: Eyes shift within the dark faceplate to reinforce gaze direction.
- **Damping**: Linear interpolation via delta time in R3F `useFrame` loop (`smooth = min(1, delta * 5)`).
- **Hero-wide Listener**: Cursor position calculated relative to the robot's head center across the entire hero section.
- **Fallback**: High-fidelity CSS/SVG representation of yellow helmet, dark visor, and glowing eyes when WebGL is unsupported or disabled.
