// Mirrors backend/app/schema.py. Keep the two in sync by hand.
export type SceneType = "title_card" | "diagram" | "code_walkthrough" | "step_list";
export type Level = "beginner" | "intermediate";
export type LanguageCode = "en" | "hi" | "kn";

export interface Scene {
  type: SceneType;
  heading: string;
  narration: string;
  subtitle?: string | null;
  code?: string | null;
  highlight_lines: number[];
  items: string[];
}

export interface Lesson {
  title: string;
  level: Level;
  language: LanguageCode;
  scenes: Scene[];
}

export interface GenerateRequest {
  topic: string;
  level: Level;
  language: LanguageCode;
  target_seconds: number;
}

export interface GenerateResponse {
  request: GenerateRequest;
  source: "fallback" | "llm";
  lesson: Lesson;
}

// Part 1b has a separate, audio-derived timeline. Do not add timing fields to Scene.
export type SampleLanguage = "en" | "hi";
export type GeneratedLanguage = "en" | "hi" | "kn";

export interface TimedScene {
  index: number;
  start_seconds: number;
  audio_seconds: number;
  duration_seconds: number;
  audio_url: string;
  cues?: NarrationCue[];
}

export interface NarrationCue {
  label?: string;
  text: string;
  start_seconds: number;
  end_seconds: number;
  item_index: number | null;
  item_indices?: number[];
  highlight_lines: number[];
}

export interface SampleTimeline {
  kind?: "generated";
  lesson_id?: string;
  source_lesson_id?: string;
  subtitle_url?: string;
  language: SampleLanguage | GeneratedLanguage;
  voice: string;
  sample_rate: number;
  pause_seconds: number;
  total_seconds: number;
  audio_url: string;
  lesson: Lesson;
  semantic_lesson?: Lesson;
  scenes: TimedScene[];
}

export interface ExportResult {
  video_url: string;
  fps: number;
  frames: number;
  expected_duration_seconds: number;
  duration_seconds: number;
  width: number;
  height: number;
  video_codec: string;
  audio_codec: string;
}
