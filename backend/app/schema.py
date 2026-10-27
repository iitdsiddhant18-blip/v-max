"""Data contracts for Blu Visual Teacher.

Everything the LLM returns, and everything the API accepts or returns, is
validated here. The LLM only ever produces DATA that matches these models;
our own components turn that data into visuals (hard rule: data, not code).
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

SceneType = Literal["title_card", "diagram", "code_walkthrough", "step_list"]
Level = Literal["beginner", "intermediate"]
LanguageCode = Literal["en", "hi", "kn"]


class Scene(BaseModel):
    type: SceneType
    heading: str = Field(min_length=1, max_length=120)
    narration: str = Field(min_length=1, max_length=600)
    subtitle: Optional[str] = Field(default=None, max_length=160)
    code: Optional[str] = Field(default=None, max_length=1200)
    highlight_lines: List[int] = Field(default_factory=list)  # 1-based line numbers
    items: List[str] = Field(default_factory=list, max_length=8)

    @field_validator("heading", "narration")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @model_validator(mode="after")
    def check_type_specific_fields(self) -> "Scene":
        if self.type == "code_walkthrough":
            if not self.code or not self.code.strip():
                raise ValueError("code_walkthrough scenes need non-empty code")
            n_lines = len(self.code.split("\n"))
            for line in self.highlight_lines:
                if line < 1 or line > n_lines:
                    raise ValueError(
                        f"highlight line {line} is outside the code (1..{n_lines})"
                    )
        if self.type in ("diagram", "step_list") and not self.items:
            raise ValueError(f"{self.type} scenes need at least one item")
        return self


class Lesson(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    level: Level = "beginner"
    # Language of the TEXT inside this lesson. Phase 1a lessons are English only;
    # translation to hi/kn is added in Phase 3a.
    language: LanguageCode = "en"
    scenes: List[Scene] = Field(min_length=3, max_length=6)


class GenerateRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=200)
    level: Level = "beginner"
    language: LanguageCode = "en"
    target_seconds: int = Field(default=60, ge=30, le=90)

    @field_validator("topic")
    @classmethod
    def strip_topic(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("topic must have at least 2 characters")
        return v


class GenerateResponse(BaseModel):
    request: GenerateRequest
    source: Literal["fallback", "llm"]
    lesson: Lesson
