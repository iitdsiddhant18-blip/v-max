from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.generic_fallback import make_generic_fallback
from backend.app.fallback import load_fallback_lesson

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_generate_returns_a_topic_specific_fallback_and_echoes_the_request(monkeypatch):
    monkeypatch.setattr("backend.app.main.plan_lesson",
                        lambda req: ("fallback", make_generic_fallback(req)))
    body = {"topic": "How does a Python loop work?", "level": "beginner",
            "language": "kn", "target_seconds": 45}
    r = client.post("/api/generate", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["source"] == "fallback"
    assert data["request"] == body
    assert "Python loop" in data["lesson"]["title"]
    assert len(data["lesson"]["scenes"]) == 3
    # Part 2a plans English; translation comes in Part 3a.
    assert data["lesson"]["language"] == "en"


def test_generate_uses_defaults_when_only_topic_is_given(monkeypatch):
    monkeypatch.setattr("backend.app.main.plan_lesson",
                        lambda req: ("fallback", make_generic_fallback(req)))
    r = client.post("/api/generate", json={"topic": "photosynthesis"})
    assert r.status_code == 200
    req = r.json()["request"]
    assert (req["level"], req["language"], req["target_seconds"]) == ("beginner", "en", 60)


def test_generate_returns_a_valid_llm_response_when_planner_succeeds(monkeypatch):
    monkeypatch.setattr("backend.app.main.plan_lesson",
                        lambda req: ("llm", load_fallback_lesson()))
    r = client.post("/api/generate", json={"topic": "Python loops"})
    assert r.status_code == 200
    assert r.json()["source"] == "llm"
    assert r.json()["lesson"]["title"] == "How a Python loop works"


def test_generate_rejects_unsupported_language_with_422():
    r = client.post("/api/generate", json={"topic": "loops", "language": "ta"})
    assert r.status_code == 422


def test_generate_rejects_target_below_30_with_422():
    r = client.post("/api/generate", json={"topic": "loops", "target_seconds": 10})
    assert r.status_code == 422


def test_generate_rejects_empty_topic_with_422():
    r = client.post("/api/generate", json={"topic": ""})
    assert r.status_code == 422


def test_generate_rejects_missing_topic_with_422():
    r = client.post("/api/generate", json={"language": "en"})
    assert r.status_code == 422


def test_cors_allows_the_vite_dev_origin():
    r = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
