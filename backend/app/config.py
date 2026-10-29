from functools import cached_property
from pathlib import Path
from urllib.parse import urlsplit
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore")

    # App
    app_env: str = "development"
    backend_port: int = 8000
    cors_allow_origins: str = "http://localhost:5500,http://127.0.0.1:5500"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # LLM Provider
    llm_provider: str = "openai"
    naito_base_url: str = ""
    naito_api_key: str = ""
    naito_model: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""
    supabase_db_url: str = ""

    rag_collection: str = "knowledge"
    rag_top_k: int = Field(default=5, ge=1, le=20)
    rag_similarity_threshold: float = Field(default=0.35, ge=-1, le=1)
    rag_embedding_dimension: int = Field(default=1536, ge=1)
    rag_system_prompt: str = "등록된 자료를 바탕으로 질문에 답하는 도우미입니다."

    @cached_property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def rag_enabled(self) -> bool:
        return bool(self.supabase_db_url.strip())

    def configuration_report(self, feature: str = "app") -> dict:
        """Check presence and basic format only; never return values or call services.

        app selects rag when a DB is configured, otherwise basic. Auth includes
        the frontend public key; a secret/service-role key is not needed for JWKS.
        """
        profile = ("rag" if self.rag_enabled else "basic") if feature == "app" else feature
        required = {
            "basic": [],
            "ingest": ["openai_api_key", "supabase_db_url"],
            "rag": ["openai_api_key", "supabase_db_url"],
            "llm": [],
            "auth": ["supabase_url", "supabase_publishable_key"],
        }
        if profile not in required:
            raise ValueError("Unknown configuration profile")
        keys = list(required[profile])
        invalid = []
        if profile in {"rag", "llm"}:
            if self.llm_provider == "openai":
                keys += ["openai_api_key", "openai_model"]
            elif self.llm_provider == "naito":
                keys += ["naito_base_url", "naito_api_key", "naito_model"]
            else:
                invalid.append("llm_provider")
        missing = [key for key in dict.fromkeys(keys) if not getattr(self, key).strip()]
        for key in keys:
            if key in missing:
                continue
            schemes = {
                "supabase_db_url": {"postgres", "postgresql", "postgresql+psycopg2"},
                "supabase_url": {"http", "https"}, "naito_base_url": {"http", "https"},
            }.get(key)
            if schemes:
                try:
                    url = urlsplit(getattr(self, key))
                    valid = url.scheme in schemes and bool(url.hostname)
                except ValueError:
                    valid = False
                if not valid:
                    invalid.append(key)
        return {"profile": profile, "ready": not missing and not invalid,
                "missing": missing, "invalid": list(dict.fromkeys(invalid))}

    def missing_keys(self, feature: str = "app") -> list[str]:
        """Compatibility helper: names only; full diagnostics include invalid fields."""
        return self.configuration_report(feature)["missing"]


settings = Settings()
