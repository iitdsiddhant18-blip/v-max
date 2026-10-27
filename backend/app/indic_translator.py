"""Local offline IndicTrans2 translation adapter for Hindi and Kannada.

Follows the tested preflight configuration using IndicTransToolkit.processor.IndicProcessor
and local-only Hugging Face cache.
Designed for 4GB VRAM GPU lifecycle: unloads Ollama, translates in small batches,
and frees GPU tensors so Parler-TTS or other models have full access to VRAM.
"""
import gc
import json
import os
import re
import sys
import urllib.request
from typing import ClassVar

import torch

from .translated_lesson import clean_text

LANG_TAGS = {"hi": "hin_Deva", "kn": "kan_Knda"}
MODEL_ID = "ai4bharat/indictrans2-en-indic-dist-200M"
BATCH_SIZE = 4

# Protected glossary patterns (ordered: longer/complex expressions first)
PROTECTED_PATTERNS = [
    re.compile(r"\brange\s*\([^)]*\)", re.IGNORECASE),
    re.compile(r"\bprint\s*\([^)]*\)", re.IGNORECASE),
    re.compile(r"\blen\s*\([^)]*\)", re.IGNORECASE),
    re.compile(r"\b[a-zA-Z_]\w*\s*[\*\+\-\/\%]\s*[a-zA-Z0-9_]+"),
    re.compile(r"\b(?:Alice|Bob|Python)\b", re.IGNORECASE),
    re.compile(r"\b(?:for|while|if|def|return|import|class)\b"),
    re.compile(r"\b\d+\b"),
]

PLACEHOLDER_RE = re.compile(r"X\d+X")


def unload_ollama() -> None:
    """Request Ollama to unload models from VRAM (keep_alive: 0) to ensure full GPU budget."""
    try:
        for model in ("qwen3:4b", "llama3.2:3b"):
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=json.dumps({"model": model, "keep_alive": 0}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=2):
                pass
    except Exception:
        pass


class LocalIndicTranslator:
    """Offline translator using local cached ai4bharat/indictrans2-en-indic-dist-200M."""

    def __init__(self, model_location: str | None = None) -> None:
        self.model_location = model_location or MODEL_ID
        self._tokenizer = None
        self._model = None
        self._processor = None
        self._device = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_DATASETS_OFFLINE"] = "1"

        unload_ollama()

        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        from IndicTransToolkit.processor import IndicProcessor

        self._device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_location, trust_remote_code=True, local_files_only=True
        )
        self._model = AutoModelForSeq2SeqLM.from_pretrained(
            self.model_location, trust_remote_code=True, local_files_only=True
        ).to(self._device)
        self._model.eval()
        self._processor = IndicProcessor(inference=True)

    def unload(self) -> None:
        """Free model from GPU memory to allow Parler TTS or other models full VRAM."""
        self._model = None
        self._tokenizer = None
        self._processor = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @staticmethod
    def protect_tokens(text: str) -> tuple[str, dict[str, str]]:
        """Replace code tokens and glossary words with stable X0X placeholders."""
        mapping: dict[str, str] = {}
        counter = 0

        protected_ranges: list[tuple[int, int, str]] = []
        for pattern in PROTECTED_PATTERNS:
            for match in pattern.finditer(text):
                start, end = match.span()
                if any(s < end and match.start() < e for s, e, _ in protected_ranges):
                    continue
                protected_ranges.append((start, end, match.group(0)))

        protected_ranges.sort(key=lambda r: r[0])

        parts = []
        last_idx = 0
        for start, end, token in protected_ranges:
            parts.append(text[last_idx:start])
            tag = f"X{counter}X"
            counter += 1
            mapping[tag] = token
            parts.append(tag)
            last_idx = end
        parts.append(text[last_idx:])
        return "".join(parts), mapping

    @staticmethod
    def restore_tokens(text: str, mapping: dict[str, str], language: str) -> str:
        """Restore protected tokens and verify no placeholder was lost or damaged."""
        result = text
        for tag, original in mapping.items():
            if tag not in result:
                raise ValueError(
                    f"Protected token placeholder '{tag}' ({original}) lost during translation: '{text}'"
                )
            result = result.replace(tag, original)

        # Standardize "value" in Hindi to "मान" if "मूल्य" appears in coding contexts
        if language == "hi":
            result = re.sub(r"\bमूल्य\b", "मान", result)

        return clean_text(result)

    def translate_many(self, english_texts: list[str], language: str) -> list[str]:
        """Translate a batch of English texts to Hindi ('hi') or Kannada ('kn')."""
        if language not in LANG_TAGS:
            raise ValueError(f"Unsupported language '{language}'. Expected 'hi' or 'kn'.")
        if not english_texts:
            return []

        self._ensure_loaded()
        target_tag = LANG_TAGS[language]

        # 1. Protect code tokens and keywords
        masked_texts: list[str] = []
        mappings: list[dict[str, str]] = []
        for text in english_texts:
            masked, mapping = self.protect_tokens(text)
            masked_texts.append(masked)
            mappings.append(mapping)

        # 2. Process in bounded mini-batches to prevent 4GB VRAM exhaustion
        postprocessed: list[str] = []
        for i in range(0, len(masked_texts), BATCH_SIZE):
            chunk = masked_texts[i : i + BATCH_SIZE]
            batch = self._processor.preprocess_batch(
                chunk, src_lang="eng_Latn", tgt_lang=target_tag
            )
            inputs = self._tokenizer(
                batch,
                truncation=True,
                padding="longest",
                return_tensors="pt",
                return_attention_mask=True,
            ).to(self._device)

            with torch.no_grad():
                generated = self._model.generate(
                    **inputs, num_beams=5, max_length=256, use_cache=False
                )

            decoded = self._tokenizer.batch_decode(
                generated, skip_special_tokens=True, clean_up_tokenization_spaces=True
            )
            chunk_post = self._processor.postprocess_batch(decoded, lang=target_tag)
            postprocessed.extend(chunk_post)

        # 3. Release GPU memory immediately after generation so subsequent models have full VRAM
        self.unload()

        if len(postprocessed) != len(english_texts):
            raise ValueError("Translator returned mismatched item count")

        # 4. Restore protected tokens and clean text
        results: list[str] = []
        for raw, mapping in zip(postprocessed, mappings):
            restored = self.restore_tokens(raw, mapping, language)
            results.append(restored)

        return results
