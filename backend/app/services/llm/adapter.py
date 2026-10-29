from langchain_core.language_models import BaseChatModel
from app.config import settings
from app.core.exceptions import ConfigurationError


def get_llm(streaming: bool = False) -> BaseChatModel:
    """
    LLM_PROVIDER 환경변수로 provider 선택.
    openai | naito — 코드 변경 없이 .env만 변경.
    """
    if settings.llm_provider == "naito":
        from app.services.llm.naito import build_naito_llm
        return build_naito_llm(streaming=streaming)

    if settings.llm_provider != "openai":
        raise ConfigurationError("LLM_PROVIDER는 openai 또는 naito로 설정해 주세요.")
    if not settings.openai_api_key:
        raise ConfigurationError("답변 생성용 OPENAI_API_KEY가 설정되지 않았습니다.")

    from app.services.llm.openai import build_openai_llm
    return build_openai_llm(streaming=streaming)


def get_embedding_model():
    if not settings.openai_api_key:
        raise ConfigurationError("문서 임베딩용 OPENAI_API_KEY가 설정되지 않았습니다.")
    """OpenAI Embeddings — RAG 전용."""
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
        request_timeout=30,
        max_retries=1,
    )
