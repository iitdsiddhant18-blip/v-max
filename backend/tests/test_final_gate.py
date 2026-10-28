"""Final-demo regressions: no misleading localized completion or corrupt cache."""
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.localized_media import load_localized, localized_folder, prepare_localized
from backend.app.localized_export import export_localized
from backend.tests.test_localized_media import FakeTranslator, make_fake_synthesize, prepared_english


def test_localized_api_enforces_duration(monkeypatch):
    arguments = {}

    def fake_prepare(source_id, language, **kwargs):
        arguments.update(kwargs)
        return {"language": language, "source_lesson_id": source_id}

    monkeypatch.setattr("backend.app.main.prepare_localized", fake_prepare)
    response = TestClient(app).post("/api/localized/prepare", json={
        "source_lesson_id": "a" * 64, "language": "hi",
    })
    assert response.status_code == 200
    assert arguments["enforce_duration"] is True


def test_short_localized_audio_fails_before_publishing(prepared_english):
    source_id, eng_root, localized_root = prepared_english
    with pytest.raises(ValueError, match="30–90"):
        prepare_localized(source_id, "hi", translator=FakeTranslator(),
                          synthesize=make_fake_synthesize(), root=localized_root,
                          source_root=eng_root, enforce_duration=True)
    assert not list(localized_root.glob("*/timeline.json"))


def test_cached_manifest_tampering_is_rejected(prepared_english):
    source_id, eng_root, localized_root = prepared_english
    manifest = prepare_localized(source_id, "hi", translator=FakeTranslator(),
                                  synthesize=make_fake_synthesize(), root=localized_root,
                                  source_root=eng_root)
    folder = localized_folder(manifest["lesson_id"], localized_root)
    path = folder / "timeline.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["lesson"]["title"] = "A different topic"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_localized(manifest["lesson_id"], root=localized_root)


def test_short_cached_audio_cannot_be_exported(prepared_english, tmp_path):
    source_id, eng_root, localized_root = prepared_english
    manifest = prepare_localized(source_id, "kn", translator=FakeTranslator(),
                                  synthesize=make_fake_synthesize(), root=localized_root,
                                  source_root=eng_root)
    with pytest.raises(ValueError, match="duration"):
        export_localized(manifest["lesson_id"], root=localized_root,
                         output_root=tmp_path / "exports")
