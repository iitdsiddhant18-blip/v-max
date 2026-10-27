"""Smoke test against a RUNNING server.

Usage:
  python backend/scripts/smoke_http.py                       # backend on :8000
  python backend/scripts/smoke_http.py http://127.0.0.1:5173 # through the Vite proxy
"""
import sys

import requests

base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"

health = requests.get(f"{base}/api/health", timeout=10)
print("health:", health.status_code, health.json())

body = {"topic": "How does a Python loop work?", "level": "beginner",
        "language": "hi", "target_seconds": 60}
gen = requests.post(f"{base}/api/generate", json=body, timeout=30)
data = gen.json()
print("generate:", gen.status_code, data["source"], data["lesson"]["title"],
      len(data["lesson"]["scenes"]), "scenes")
print("scene types:", [s["type"] for s in data["lesson"]["scenes"]])

bad = requests.post(f"{base}/api/generate", json={"topic": "loops", "language": "ta"}, timeout=10)
print("bad language:", bad.status_code)
