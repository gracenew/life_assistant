from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/config")
def public_config():
    return {
        "ai_provider": settings.ai_provider,
        "ai_model": settings.default_model,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
        "openrouter_base_url": settings.openrouter_base_url,
    }
