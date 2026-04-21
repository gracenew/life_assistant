from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any, Optional
import re

from sqlalchemy.orm import Session

from app import ai_service
from app.context_builder import build_data_summary
from app.tools.base import ToolContext
from app.tools.registry import execute_tool, get_tool_schema_lines

AGENT_SYSTEM_PROMPT = """你是用户的本地生活助理 Agent。
你的任务是根据用户问题，判断是否需要调用工具，并在需要时一步一步调用工具。

规则：
1. 你必须只输出 JSON，不要输出额外解释。
2. 如果已经有足够信息，请输出：
{"type":"final","answer":"...","reasoning":"简短说明"}
3. 如果需要调用工具，请输出：
{"type":"tool","tool":"工具名","arguments":{...},"reasoning":"为什么要调用"}
4. 优先在这些场景使用工具：
   - 实时外部信息：天气、网页搜索
   - 本地数据查询：任务列表
   - 用户要求创建任务：先调用 create_task_preview，不直接假装已创建
5. 不要编造工具结果，不知道就调用工具。
6. 一次只调用一个工具。
"""

WEATHER_COMPLEX_HINTS = ("如果", "提醒", "任务", "日程", "创建", "新建", "顺便", "然后", "并且", "再帮我")
TASK_COMPLEX_HINTS = ("创建", "新建", "添加", "完成", "删除", "修改", "更新", "提醒", "安排")
LOCATION_STOPWORDS = {
    "今天",
    "明天",
    "后天",
    "天气",
    "查询",
    "查看",
    "帮我",
    "一下",
    "请问",
    "现在",
    "当地",
    "未来",
}
LOCATION_PREFIX_PATTERN = re.compile(r"^(帮我|请|麻烦|查一下|查|查看|看看|看下|一下|现在|想知道|告诉我)+")
LOCATION_NOISE_PATTERN = re.compile(r"^(一下|下|的)+")


def _extract_json_block(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("模型未返回可解析 JSON")
    return json.loads(text[start : end + 1])


def _summarize_tool_result(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return result.get("error") or "工具调用失败"
    data = result.get("data")
    if isinstance(data, dict):
        preview = {k: data[k] for k in list(data.keys())[:4]}
        return json.dumps(preview, ensure_ascii=False)
    return json.dumps(data, ensure_ascii=False)


def _extract_weather_date(message: str) -> str:
    if "后天" in message:
        return (date.today() + timedelta(days=2)).isoformat()
    if "明天" in message:
        return "tomorrow"
    return "today"


def _extract_weather_location(message: str) -> str:
    patterns = [
        r"(?:今天|明天|后天)?([A-Za-z\u4e00-\u9fff]{2,12}?)(?:的)?天气",
        r"([A-Za-z\u4e00-\u9fff]{2,12}?)(?:今天|明天|后天)?(?:的)?天气",
        r"(?:查询|查看|查|看看)([A-Za-z\u4e00-\u9fff]{2,12}?)(?:今天|明天|后天)?天气",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if not match:
            continue
        candidate = match.group(1).strip("，。,.？?！! ")
        candidate = LOCATION_PREFIX_PATTERN.sub("", candidate)
        candidate = LOCATION_NOISE_PATTERN.sub("", candidate)
        candidate = candidate.strip("，。,.？?！! ")
        candidate = re.sub(r"^(今天|明天|后天)", "", candidate)
        candidate = re.sub(r"(今天|明天|后天)$", "", candidate)
        candidate = candidate.strip()
        if candidate and candidate not in LOCATION_STOPWORDS:
            return candidate
    return ""


def _is_simple_weather_query(message: str) -> bool:
    if "天气" not in message:
        return False
    return not any(token in message for token in WEATHER_COMPLEX_HINTS)


def _is_simple_task_query(message: str) -> bool:
    if not any(token in message for token in ("待办", "任务")):
        return False
    if not any(token in message for token in ("哪些", "看看", "查看", "列出", "当前", "现在", "最靠前", "有哪些")):
        return False
    return not any(token in message for token in TASK_COMPLEX_HINTS)


async def _run_direct_tool_route(message: str, context: ToolContext) -> Optional[dict[str, Any]]:
    if _is_simple_weather_query(message):
        location = _extract_weather_location(message)
        if location:
            requested_date = _extract_weather_date(message)
            try:
                result = await execute_tool("weather", {"location": location, "date": requested_date}, context)
            except Exception as exc:  # noqa: BLE001
                result = {
                    "ok": False,
                    "tool": "weather",
                    "input": {"location": location, "date": requested_date},
                    "data": None,
                    "error": f"天气工具暂时不可用：{exc!s}",
                }
            if result.get("ok"):
                data = result["data"]
                answer = (
                    f"{data['location']}{'明天' if data['date'] == 'tomorrow' else '今天'}天气："
                    f"{data['condition']}，气温 {data['min_temp_c']}-{data['max_temp_c']}C。"
                    f"{data['advice']}"
                )
            else:
                answer = result.get("error") or "天气查询失败"
            return {
                "answer": answer,
                "reasoning": "direct_tool: weather",
                "tool_calls": [
                    {
                        "tool": "weather",
                        "arguments": {"location": location, "date": requested_date},
                        "ok": result.get("ok", False),
                        "summary": _summarize_tool_result(result),
                        "error": result.get("error"),
                    }
                ],
                "pending_actions": [],
            }

    if _is_simple_task_query(message):
        try:
            result = await execute_tool("list_tasks", {"status": "pending", "limit": 8}, context)
        except Exception as exc:  # noqa: BLE001
            result = {
                "ok": False,
                "tool": "list_tasks",
                "input": {"status": "pending", "limit": 8},
                "data": None,
                "error": f"任务工具暂时不可用：{exc!s}",
            }
        if result.get("ok"):
            tasks = (result.get("data") or {}).get("tasks") or []
            if tasks:
                lines = [f"{idx + 1}. {item['title']}" for idx, item in enumerate(tasks[:5])]
                answer = "当前待办靠前的几项是：\n" + "\n".join(lines)
            else:
                answer = "当前没有未完成的待办任务。"
        else:
            answer = result.get("error") or "任务查询失败"
        return {
            "answer": answer,
            "reasoning": "direct_tool: list_tasks",
            "tool_calls": [
                {
                    "tool": "list_tasks",
                    "arguments": {"status": "pending", "limit": 8},
                    "ok": result.get("ok", False),
                    "summary": _summarize_tool_result(result),
                    "error": result.get("error"),
                }
            ],
            "pending_actions": [],
        }

    return None


async def run_agent(
    *,
    db: Session,
    message: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_steps: int = 4,
) -> tuple[dict[str, Any], str, str]:
    context = ToolContext(db=db)
    direct_result = await _run_direct_tool_route(message, context)
    if direct_result is not None:
        resolved_provider = ai_service.resolve_provider(provider)
        resolved_model = ai_service.resolve_model(resolved_provider, model)
        return direct_result, resolved_provider, resolved_model

    summary = build_data_summary(db, max_lines=60)
    tool_lines = get_tool_schema_lines()
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                f"{AGENT_SYSTEM_PROMPT}\n\n"
                f"可用工具：\n{tool_lines}\n\n"
                f"本地数据摘要：\n{summary}"
            ),
        },
        {"role": "user", "content": message},
    ]

    tool_calls: list[dict[str, Any]] = []
    pending_actions: list[dict[str, Any]] = []
    final_answer = ""
    final_reasoning = ""

    resolved_provider = ai_service.resolve_provider(provider)
    resolved_model = ai_service.resolve_model(resolved_provider, model)

    for step in range(max_steps):
        raw_reply, resolved_provider, resolved_model = await ai_service.chat_completion(
            messages,
            provider=resolved_provider,
            model=resolved_model,
        )
        parsed = _extract_json_block(raw_reply)
        action_type = parsed.get("type")
        final_reasoning = parsed.get("reasoning") or final_reasoning

        if action_type == "final":
            final_answer = (parsed.get("answer") or "").strip()
            break

        if action_type != "tool":
            raise ValueError("Agent 返回了不支持的动作类型")

        tool_name = (parsed.get("tool") or "").strip()
        arguments = parsed.get("arguments") or {}
        result = await execute_tool(tool_name, arguments, context)
        tool_calls.append(
            {
                "tool": tool_name,
                "arguments": arguments,
                "ok": result.get("ok", False),
                "summary": _summarize_tool_result(result),
                "error": result.get("error"),
            }
        )

        pending_action = ((result.get("data") or {}).get("pending_action") if result.get("ok") else None)
        if pending_action:
            pending_actions.append(pending_action)

        messages.append({"role": "assistant", "content": raw_reply})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"工具 {tool_name} 已执行，结果如下：\n"
                    f"{json.dumps(result, ensure_ascii=False)}\n"
                    "请继续判断是给出最终答案，还是调用下一个工具。"
                ),
            }
        )

    if not final_answer:
        final_answer = "我已经完成了工具查询，但本轮没有形成稳定结论。请尝试把问题再具体一点。"

    return {
        "answer": final_answer,
        "reasoning": final_reasoning,
        "tool_calls": tool_calls,
        "pending_actions": pending_actions,
    }, resolved_provider, resolved_model


def confirm_action(db: Session, action_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    if action_type != "create_task":
        raise ValueError(f"暂不支持确认动作：{action_type}")

    from app import models

    title = (payload.get("title") or "").strip()
    if not title:
        raise ValueError("title 不能为空")

    due_at = payload.get("due_at")
    if due_at:
        due_at = datetime.fromisoformat(due_at.replace("Z", "+00:00"))

    task = models.Task(
        title=title,
        description=payload.get("description"),
        priority=payload.get("priority") or "medium",
        status="pending",
        due_at=due_at,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {
        "ok": True,
        "action_type": action_type,
        "record": {
            "id": task.id,
            "title": task.title,
            "priority": task.priority,
            "status": task.status,
            "due_at": task.due_at.isoformat() if task.due_at else None,
        },
    }
