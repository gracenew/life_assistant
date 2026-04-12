import httpx
from typing import Optional

from app.config import settings
from app import ollama_client, openrouter_client


def resolve_provider(provider: Optional[str] = None) -> str:
    p = (provider or settings.ai_provider or "ollama").strip().lower()
    if p not in {"ollama", "openrouter"}:
        raise ValueError(f"不支持的 AI Provider：{p}")
    return p


def resolve_model(provider: str, model: Optional[str] = None) -> str:
    if model and model.strip():
        return model.strip()
    if provider == "openrouter":
        return settings.default_model if settings.ai_provider == "openrouter" else "openai/gpt-4o-mini"
    return settings.ollama_model


async def chat_completion(
    messages: list,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> tuple[str, str, str]:
    resolved_provider = resolve_provider(provider)
    resolved_model = resolve_model(resolved_provider, model)

    if resolved_provider == "openrouter":
        reply = await openrouter_client.chat_completion(messages, model=resolved_model)
    else:
        reply = await ollama_client.chat_completion(messages, model=resolved_model)

    return reply, resolved_provider, resolved_model


def provider_error_message(provider: str, err: Exception) -> str:
    if provider == "openrouter":
        if isinstance(err, httpx.RequestError):
            return f"无法连接 OpenRouter（{settings.openrouter_base_url}）。请检查网络或服务可用性。详情：{err!s}"
        return str(err)
    if isinstance(err, httpx.RequestError):
        return f"无法连接 Ollama（{settings.ollama_base_url}）。请确认已运行 Ollama 且模型已下载。详情：{err!s}"
    return str(err)
