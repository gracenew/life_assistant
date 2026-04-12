from typing import Optional

import httpx

from app.config import settings


async def chat_completion(
    messages: list,
    *,
    model: Optional[str] = None,
    timeout: float = 120.0,
) -> str:
    if not settings.openrouter_api_key:
        raise RuntimeError("未配置 OPENROUTER_API_KEY")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    if settings.openrouter_site_url:
        headers["HTTP-Referer"] = settings.openrouter_site_url
    if settings.openrouter_app_name:
        headers["X-Title"] = settings.openrouter_app_name

    payload = {
        "model": model or settings.default_model,
        "messages": messages,
    }

    url = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        msg = choices[0].get("message") or {}
        content = msg.get("content") or ""
        if isinstance(content, list):
            text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
            return "".join(text_parts).strip()
        return str(content).strip()
