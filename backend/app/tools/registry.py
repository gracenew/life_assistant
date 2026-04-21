from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.tools.base import ToolContext
from app.tools import system_tools, web_tools


ToolExecutor = Callable[[dict[str, Any], ToolContext], Awaitable[dict[str, Any]]]


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    executor: ToolExecutor


TOOL_DEFINITIONS: dict[str, ToolDefinition] = {
    "web_search": ToolDefinition(
        name="web_search",
        description="搜索互联网公开信息，适合查网页、概念、官网链接、新闻线索。",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "limit": {"type": "integer", "description": "返回结果数量，建议 3-5", "default": 5},
            },
            "required": ["query"],
        },
        executor=web_tools.web_search,
    ),
    "weather": ToolDefinition(
        name="weather",
        description="查询指定地点的天气，适合今天/明天出行判断。",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "地点，如上海、北京、Hangzhou"},
                "date": {"type": "string", "description": "today、tomorrow 或 YYYY-MM-DD", "default": "today"},
            },
            "required": ["location"],
        },
        executor=web_tools.weather,
    ),
    "list_tasks": ToolDefinition(
        name="list_tasks",
        description="读取系统中的任务列表，适合查看待办、逾期任务、近期任务。",
        parameters={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "可选 pending 或 done"},
                "limit": {"type": "integer", "description": "返回任务数量，默认 8", "default": 8},
            },
            "required": [],
        },
        executor=system_tools.list_tasks,
    ),
    "create_task_preview": ToolDefinition(
        name="create_task_preview",
        description="生成创建任务的预览，不直接写入数据库，适合先让用户确认。",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "任务标题"},
                "description": {"type": "string", "description": "任务备注"},
                "priority": {"type": "string", "description": "low、medium、high", "default": "medium"},
                "due_at": {"type": "string", "description": "ISO 时间字符串，可为空"},
            },
            "required": ["title"],
        },
        executor=system_tools.create_task_preview,
    ),
}


def get_tool_schema_lines() -> str:
    lines: list[str] = []
    for tool in TOOL_DEFINITIONS.values():
        lines.append(f"- {tool.name}: {tool.description}")
        lines.append(f"  参数模式: {tool.parameters}")
    return "\n".join(lines)


async def execute_tool(name: str, arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    tool = TOOL_DEFINITIONS.get(name)
    if not tool:
        return {"ok": False, "tool": name, "input": arguments, "data": None, "error": f"未注册工具：{name}"}
    return await tool.executor(arguments, context)
