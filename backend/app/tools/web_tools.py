from __future__ import annotations

import re
from datetime import date as date_cls
from html import unescape
from typing import Any
from urllib.parse import parse_qs, quote_plus, urlparse

import httpx

from app.tools.base import ToolContext

LOCATION_CLEANUP_PATTERN = re.compile(r"^(帮我|请|麻烦|查一下|查|查看|看看|看下|一下|下|的)+")


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", unescape(text or "")).strip()


def _decode_duckduckgo_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    uddg = query.get("uddg")
    if uddg:
        return unescape(uddg[0])
    if url.startswith("//"):
        return f"https:{url}"
    return url


def _normalize_weather_location(location: str) -> str:
    cleaned = (location or "").strip()
    cleaned = LOCATION_CLEANUP_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"^(今天|明天|后天)", "", cleaned)
    cleaned = re.sub(r"(今天|明天|后天)$", "", cleaned)
    return cleaned.strip("，。,.？?！! ")


async def web_search(arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    query = (arguments.get("query") or "").strip()
    if not query:
        return {"ok": False, "tool": "web_search", "input": arguments, "data": None, "error": "query 不能为空"}

    limit = min(max(int(arguments.get("limit", 5) or 5), 1), 8)
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ai-life-assistant/1.0)"}

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        html = response.text

    blocks = re.findall(r'<div class="result results_links[^"]*?">(.*?)</div>\s*</div>', html, re.S)
    results: list[dict[str, Any]] = []
    for block in blocks:
        title_match = re.search(r'class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not title_match:
            continue
        snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</a>', block, re.S)
        results.append(
            {
                "title": _strip_tags(title_match.group(2)),
                "url": _decode_duckduckgo_url(title_match.group(1)),
                "snippet": _strip_tags(snippet_match.group(1) if snippet_match else ""),
            }
        )
        if len(results) >= limit:
            break

    return {
        "ok": True,
        "tool": "web_search",
        "input": {"query": query, "limit": limit},
        "data": {"results": results, "count": len(results)},
        "error": None,
    }


def _pick_weather_day(requested: str) -> tuple[int, str]:
    raw = (requested or "today").strip().lower()
    if raw == "tomorrow":
        return 1, "tomorrow"
    if raw in {"today", ""}:
        return 0, "today"
    try:
        target = date_cls.fromisoformat(raw)
        delta = (target - date_cls.today()).days
        if delta < 0:
            return 0, raw
        return min(delta, 2), raw
    except ValueError:
        return 0, raw


async def weather(arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    location = _normalize_weather_location(arguments.get("location") or "")
    if not location:
        return {"ok": False, "tool": "weather", "input": arguments, "data": None, "error": "location 不能为空"}

    requested_date = (arguments.get("date") or "today").strip()
    day_index, normalized_date = _pick_weather_day(requested_date)
    url = f"https://wttr.in/{quote_plus(location)}?format=j1"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, headers={"User-Agent": "ai-life-assistant/1.0"})
        if response.status_code >= 500:
            return {
                "ok": False,
                "tool": "weather",
                "input": {"location": location, "date": requested_date},
                "data": None,
                "error": f"天气服务暂时不可用（{response.status_code}），请稍后重试或换一个城市名称再试。",
            }
        response.raise_for_status()
        payload = response.json()

    weather_days = payload.get("weather") or []
    current = payload.get("current_condition") or [{}]
    day = weather_days[min(day_index, len(weather_days) - 1)] if weather_days else {}
    hourly = day.get("hourly") or []
    first_hour = hourly[0] if hourly else {}
    summary = {
        "location": location,
        "date": normalized_date,
        "condition": ((first_hour.get("weatherDesc") or current[0].get("weatherDesc") or [{"value": ""}])[0].get("value", "")),
        "temp_c": current[0].get("temp_C"),
        "max_temp_c": day.get("maxtempC"),
        "min_temp_c": day.get("mintempC"),
        "chance_of_rain": first_hour.get("chanceofrain"),
    }
    summary["advice"] = "建议带伞" if int(summary.get("chance_of_rain") or 0) >= 50 else "暂不需要特别的降雨准备"

    return {
        "ok": True,
        "tool": "weather",
        "input": {"location": location, "date": requested_date},
        "data": summary,
        "error": None,
    }
