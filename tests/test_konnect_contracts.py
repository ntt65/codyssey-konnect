"""KONNECT evidence-gate contracts adapted to the generic RAG API.

Storage and model boundaries are fakes; ingestion, retrieval and API are real.
This does not validate vecs, network access or actual model output.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.rag import ingest, retrieve, store


@pytest.mark.parametrize("mode", ["answered", "no_evidence", "model_failure"])
def test_document_to_question_api(tmp_path, monkeypatch, mode):
    monkeypatch.setattr(settings, "supabase_db_url", "offline-test")
    monkeypatch.setattr(settings, "openai_api_key", "offline-test")
    monkeypatch.setattr(settings, "rag_embedding_dimension", 1)
    monkeypatch.setattr(settings, "rag_collection", "konnect_review_only")
    monkeypatch.setattr(settings, "rag_similarity_threshold", 0.35)
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "manual.txt").write_text("체크인은 오후 세 시입니다.", encoding="utf-8")
    saved = {}

    def replace(name, source, records):
        assert name == "konnect_review_only"
        saved[source] = records

    def query(vector, name):
        assert vector == [1.0]
        assert name == "konnect_review_only"
        distance = 0.9 if mode == "no_evidence" else 0.1
        return [(key, distance, metadata)
                for records in saved.values() for key, _, metadata in records]

    monkeypatch.setattr(ingest, "embed_documents", AsyncMock(return_value=[[1.0]]))
    monkeypatch.setattr(retrieve, "embed_query", AsyncMock(return_value=[1.0]))
    monkeypatch.setattr(store, "replace_document", replace)
    monkeypatch.setattr(store, "create_index", Mock())
    monkeypatch.setattr(store, "query", query)
    model = SimpleNamespace(ainvoke=AsyncMock(
        side_effect=RuntimeError("PRIVATE_PROVIDER_DETAIL") if mode == "model_failure" else None,
        return_value=SimpleNamespace(content="오후 세 시입니다. [1]"),
    ))
    provider = Mock(return_value=model)
    monkeypatch.setattr(retrieve, "get_llm", provider)

    assert asyncio.run(ingest.ingest(tmp_path)) == 1
    response = TestClient(app).post("/api/ask", json={"question": "체크인은 언제인가요?"})
    payload = response.json()
    if mode == "model_failure":
        assert response.status_code == 503
        assert payload["ok"] is False
        assert "PRIVATE_PROVIDER_DETAIL" not in response.text
        return
    assert response.status_code == 200
    assert payload["ok"] is True
    data = payload["data"]
    assert data["status"] == mode
    if mode == "no_evidence":
        assert data["grounded"] is False
        assert data["citations"] == []
        provider.assert_not_called()
    else:
        assert data["grounded"] is True
        assert data["sources_count"] == 1
        assert data["citations"][0]["source"] == "docs/manual.txt"
        assert "오후 세 시" in data["citations"][0]["snippet"]
        messages = model.ainvoke.call_args.args[0]
        assert "체크인은 오후 세 시" in messages[1].content


def test_konnect_evidence_filter_contract(monkeypatch):
    """Preserve the old above-threshold filtering and descending ranking rule."""
    monkeypatch.setattr(settings, "supabase_db_url", "offline-test")
    monkeypatch.setattr(settings, "openai_api_key", "offline-test")
    monkeypatch.setattr(settings, "rag_similarity_threshold", 0.35)
    monkeypatch.setattr(retrieve, "embed_query", AsyncMock(return_value=[1.0]))
    monkeypatch.setattr(store, "query", Mock(return_value=[
        ("mid", 0.5, {"text": "mid", "source": "mid.txt"}),
        ("low", 0.9, {"text": "low", "source": "low.txt"}),
        ("high", 0.1, {"text": "high", "source": "high.txt"}),
    ]))
    results = asyncio.run(retrieve.search_knowledge("question"))
    assert [row["source"] for row in results] == ["high.txt", "mid.txt"]
    assert [row["similarity"] for row in results] == pytest.approx([0.9, 0.5])
