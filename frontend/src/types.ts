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
