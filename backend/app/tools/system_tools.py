from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app import models
from app.tools.base import ToolContext


def _serialize_task(task: models.Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_at": task.due_at.isoformat() if task.due_at else None,
    }


async def list_tasks(arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    db: Session = context.db
    limit = min(max(int(arguments.get("limit", 8) or 8), 1), 20)
    status = (arguments.get("status") or "").strip() or None

    query = db.query(models.Task).order_by(models.Task.due_at.asc().nulls_last(), models.Task.id.desc())
    if status:
        query = query.filter(models.Task.status == status)
    tasks = query.limit(limit).all()
    return {
        "ok": True,
        "tool": "list_tasks",
        "input": {"status": status, "limit": limit},
        "data": {"tasks": [_serialize_task(task) for task in tasks], "count": len(tasks)},
        "error": None,
    }


async def create_task_preview(arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    title = (arguments.get("title") or "").strip()
    if not title:
        return {
            "ok": False,
            "tool": "create_task_preview",
            "input": arguments,
            "data": None,
            "error": "title 不能为空",
        }

    payload = {
        "title": title,
        "description": (arguments.get("description") or "").strip() or None,
        "priority": (arguments.get("priority") or "medium").strip() or "medium",
        "status": "pending",
        "due_at": (arguments.get("due_at") or "").strip() or None,
    }
    return {
        "ok": True,
        "tool": "create_task_preview",
        "input": arguments,
        "data": {
            "preview": payload,
            "pending_action": {"type": "create_task", "payload": payload},
        },
        "error": None,
    }
