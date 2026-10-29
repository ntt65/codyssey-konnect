from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    config = settings.configuration_report()
    return {
        "ok": True,
        "env": settings.app_env,
        "llm_provider": settings.llm_provider,
        "rag": settings.rag_enabled,
        "config": "ok" if config["ready"] else f"missing: {config['missing']}; invalid: {config['invalid']}",
        "configuration": config,
    }
