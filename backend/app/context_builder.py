"""Build a short text summary of local data for the LLM system prompt."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def build_data_summary(db: Session, *, max_lines: int = 80) -> str:
    now = _now_utc()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today_start + timedelta(days=1)
    week_ahead = today_start + timedelta(days=7)

    lines: list[str] = []

    pending = db.scalars(
        select(models.Task)
        .where(models.Task.status == "pending")
        .order_by(models.Task.due_at.asc().nulls_last(), models.Task.id.desc())
        .limit(15)
    ).all()
    lines.append(f"待办（未完成）共 {len(pending)} 条（最多列出15条）：")
    for t in pending:
        due = f" 截止 {t.due_at.isoformat()}" if t.due_at else ""
        lines.append(f"- [任务#{t.id}] {t.title}{due} 优先级:{t.priority}")

    evs = db.scalars(
        select(models.CalendarEvent)
        .where(models.CalendarEvent.start_at >= today_start, models.CalendarEvent.start_at < week_ahead)
        .order_by(models.CalendarEvent.start_at.asc())
        .limit(20)
    ).all()
    lines.append("")
    lines.append(f"未来7天日程（{len(evs)} 条）：")
    for e in evs:
        lines.append(f"- [日程#{e.id}] {e.title} 开始 {e.start_at.isoformat()}")

    habits = db.scalars(select(models.Habit).order_by(models.Habit.id.desc()).limit(20)).all()
    lines.append("")
    lines.append(f"习惯列表（{len(habits)} 个）：")
    for h in habits:
        lines.append(f"- [习惯#{h.id}] {h.name} ({h.frequency})")

    month_start = today_start.replace(day=1)
    total = db.scalar(
        select(func.coalesce(func.sum(models.Transaction.amount), 0.0)).where(
            models.Transaction.occurred_at >= month_start,
            models.Transaction.occurred_at <= now,
        )
    )
    lines.append("")
    lines.append(f"本月至今支出/收入合计（按 amount 正负，未过滤符号）：合计 {float(total or 0):.2f}")

    recent_notes = db.scalars(select(models.Note).order_by(models.Note.updated_at.desc()).limit(8)).all()
    lines.append("")
    lines.append("最近笔记：")
    for n in recent_notes:
        lines.append(f"- [笔记#{n.id}] {n.title}")

    text = "\n".join(lines)
    if len(text.splitlines()) > max_lines:
        text = "\n".join(text.splitlines()[:max_lines]) + "\n…"
    return text
