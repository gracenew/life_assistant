from typing import Optional

import httpx

from app.config import settings


async def chat_completion(
    messages: list,
    *,
    model: Optional[str] = None,
    timeout: float = 120.0,
) -> str:
    m = model or settings.ollama_model
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            url,
            json={"model": m, "messages": messages, "stream": False},
        )
        r.raise_for_status()
        data = r.json()
        msg = data.get("message") or {}
        return (msg.get("content") or "").strip()
