import pytest

from app.config import settings
from app.core.exceptions import ConfigurationError
from app.services.llm.adapter import get_embedding_model, get_llm


def test_unknown_provider_never_falls_back(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "typo")
    with pytest.raises(ConfigurationError, match="LLM_PROVIDER"):
        get_llm()


def test_missing_openai_key_is_configuration_error(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "")
    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        get_llm()
    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        get_embedding_model()
