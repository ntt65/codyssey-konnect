"""Offline smoke check: homepage, assets, health and API contracts without keys.

This deliberately disables RAG storage inside the process. It never sends real
DB, embedding, LLM or Auth requests, even when local .env credentials exist.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from app.config import settings
from app.main import app


def main():
    db_url = settings.supabase_db_url
    settings.supabase_db_url = ""
    try:
        with TestClient(app) as client:
            for path in ("/", "/health", "/docs", "/topic_demo.html", "/js/rag.js", "/js/http.js", "/css/rag.css"):
                response = client.get(path)
                assert response.status_code == 200, f"Offline route failed: {path}"
                assert response.headers.get("X-Request-ID"), f"Missing request ID: {path}"
            health = client.get("/health").json()
            assert health["configuration"]["profile"] == "basic"
            assert health["configuration"]["ready"] is True
            answer = client.post("/api/ask", json={"question": "설정 없는 화면 확인"}).json()
            assert answer["ok"] and answer["data"]["status"] == "not_configured"
            topic = client.post("/api/topic/discover", json={"query": "demo"}).json()
            assert topic["ok"] and topic["data"]["total"] == 1
            response = client.post("/api/ask", json={"question": " "})
            assert response.status_code == 422
            assert response.json()["request_id"] == response.headers["X-Request-ID"]
        print("Offline smoke passed: homepage, assets, health, docs, Topic, missing RAG and validation.")
        print("No real DB, embedding, LLM or Auth requests were made.")
        return 0
    finally:
        settings.supabase_db_url = db_url


if __name__ == "__main__":
    raise SystemExit(main())
