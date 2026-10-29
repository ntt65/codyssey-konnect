import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.config import Settings

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def config(monkeypatch):
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
    return Settings(_env_file=None)


def test_basic_mode_needs_no_auth_or_llm_keys(config):
    assert config.configuration_report() == {"profile": "basic", "ready": True, "missing": [], "invalid": []}
    assert config.missing_keys() == []


def test_rag_requires_embedding_and_database_without_auth(config):
    assert set(config.missing_keys("rag")) == {"openai_api_key", "supabase_db_url"}
    config.openai_api_key = "secret"
    config.supabase_db_url = "postgresql://user:password@localhost/db"
    assert config.configuration_report()["ready"] is True


def test_naito_still_needs_openai_embeddings_for_rag(config):
    config.llm_provider = "naito"
    config.naito_base_url = "https://example.com/v1"
    config.naito_api_key = "secret"
    config.naito_model = "model"
    assert config.configuration_report("llm")["ready"] is True
    assert set(config.missing_keys("rag")) == {"openai_api_key", "supabase_db_url"}


def test_ingest_does_not_require_answer_provider(config):
    config.openai_api_key = "secret"
    config.supabase_db_url = "postgresql://user:password@localhost/db"
    config.llm_provider = "naito"
    assert config.configuration_report("ingest")["ready"] is True
    assert config.configuration_report("rag")["ready"] is False


def test_auth_does_not_need_service_role_secret(config):
    config.supabase_url = "https://example.supabase.co"
    config.supabase_publishable_key = "public-key"
    assert config.configuration_report("auth")["ready"] is True


def test_reports_never_contain_values(config):
    config.llm_provider = "TOP_SECRET"
    report = config.configuration_report("llm")
    assert report["invalid"] == ["llm_provider"]
    assert "TOP_SECRET" not in str(report)
    config.supabase_db_url = "INVALID_TOP_SECRET"
    assert config.configuration_report("ingest")["invalid"] == ["supabase_db_url"]


def test_whitespace_is_missing(config):
    config.openai_api_key = "   "
    config.supabase_db_url = "   "
    assert config.configuration_report()["profile"] == "basic"
    assert "openai_api_key" in config.missing_keys("llm")


def test_dotenv_and_process_env_precedence(config, monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('OPENAI_API_KEY=file-secret\nSUPABASE_DB_URL=postgresql://user:pass@localhost/db\n', encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "process-secret")
    loaded = Settings(_env_file=env_file)
    assert loaded.openai_api_key == "process-secret"
    assert loaded.configuration_report("rag")["ready"] is True
    assert Settings.model_config["env_file"] == ROOT / ".env"


def test_cli_can_run_from_other_directory_and_hides_invalid_values(config, tmp_path):
    env = os.environ.copy()
    env["RAG_TOP_K"] = "TOP_SECRET"
    result = subprocess.run([sys.executable, str(ROOT / "utils/scripts/setup_dev.py")],
                            cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 2
    assert "RAG_TOP_K" in result.stdout
    assert "TOP_SECRET" not in result.stdout + result.stderr
