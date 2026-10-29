"""Regression coverage for HTTP boundaries and secret-safe developer diagnostics."""
import logging

import pytest
from fastapi.testclient import TestClient

from app.api import ask
from app.core.exceptions import AuthError, ExternalSourceError
from app.main import app


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.json()
    assert body["ok"] is False
    assert body["data"] is None
    assert body["error"]["code"] == code
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert len(body["request_id"]) == 32
    return body


@pytest.mark.parametrize(("path", "status", "code"), [
    ("/api/missing", 404, "HTTP404"), ("/api/ask", 405, "HTTP405"),
])
def test_routing_errors_are_envelopes(path, status, code):
    assert_error(TestClient(app).get(path), status, code)


def test_request_validation_names_field_without_input_values(caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    response = TestClient(app).post("/api/ask", json={"question": "TOP_SECRET" * 500})
    body = assert_error(response, 422, "ValidationError")
    assert body["error"]["issues"][0]["field"] == "body.question"
    assert body["error"]["issues"][0]["code"] == "string_too_long"
    assert "TOP_SECRET" not in response.text + caplog.text


def test_invalid_json_does_not_echo_body(caplog):
    response = TestClient(app).post("/api/ask", content='{"secret":"TOP_SECRET",',
                                   headers={"Content-Type": "application/json"})
    assert_error(response, 422, "ValidationError")
    assert "TOP_SECRET" not in response.text + caplog.text


def test_unknown_error_is_safe_traceable_and_has_cors(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    async def fail(question):
        raise RuntimeError("TOP_SECRET provider response")
    monkeypatch.setattr(ask, "answer_question", fail)
    response = TestClient(app).post("/api/ask?key=TOP_SECRET", json={"question": "TOP_SECRET"},
                                   headers={"Origin": "http://localhost:5500", "Authorization": "TOP_SECRET"})
    body = assert_error(response, 500, "InternalServerError")
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5500"
    assert "X-Request-ID" in response.headers["Access-Control-Expose-Headers"]
    assert body["request_id"] in caplog.text
    assert "RuntimeError" in caplog.text
    assert "TOP_SECRET" not in response.text + caplog.text


def test_external_failure_logs_cause_type_without_message(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    async def fail(question):
        try:
            raise RuntimeError("postgresql://TOP_SECRET")
        except RuntimeError as exc:
            raise ExternalSourceError("문서 검색에 실패했습니다.") from exc
    monkeypatch.setattr(ask, "answer_question", fail)
    response = TestClient(app).post("/api/ask", json={"question": "test"})
    assert_error(response, 503, "ExternalSourceError")
    assert "RuntimeError" in caplog.text
    assert "test_errors.py" in caplog.text
    assert "TOP_SECRET" not in response.text + caplog.text


def test_internal_model_validation_is_500_not_user_error(monkeypatch):
    async def invalid_data(question):
        return {"answer": "test"}
    monkeypatch.setattr(ask, "answer_question", invalid_data)
    assert_error(TestClient(app).post("/api/ask", json={"question": "test"}), 500, "InternalServerError")


def test_auth_error_has_bearer_challenge(monkeypatch):
    async def fail(question):
        raise AuthError()
    monkeypatch.setattr(ask, "answer_question", fail)
    response = TestClient(app).post("/api/ask", json={"question": "test"})
    assert_error(response, 401, "AuthError")
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_topic_response_uses_shared_contract():
    response = TestClient(app).post("/api/topic/discover", json={"query": "test"})
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["data"]["total"] == 1
    assert response.headers["X-Request-ID"]


def test_ids_are_new_and_not_copied_from_client():
    client = TestClient(app)
    first = client.get("/health", headers={"X-Request-ID": "untrusted"})
    second = client.get("/health")
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]
    assert first.headers["X-Request-ID"] != "untrusted"
