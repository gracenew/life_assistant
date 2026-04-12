from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app import schemas

router = APIRouter(prefix="/api/habits", tags=["habits"])


@router.get("", response_model=list[schemas.HabitOut])
def list_habits(db: Session = Depends(get_db)):
    return db.query(models.Habit).order_by(models.Habit.id.desc()).limit(200).all()


@router.post("", response_model=schemas.HabitOut)
def create_habit(body: schemas.HabitCreate, db: Session = Depends(get_db)):
    h = models.Habit(**body.model_dump())
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


@router.get("/{habit_id}", response_model=schemas.HabitOut)
def get_habit(habit_id: int, db: Session = Depends(get_db)):
    h = db.get(models.Habit, habit_id)
    if not h:
        raise HTTPException(404, "习惯不存在")
    return h


@router.patch("/{habit_id}", response_model=schemas.HabitOut)
def update_habit(habit_id: int, body: schemas.HabitUpdate, db: Session = Depends(get_db)):
    h = db.get(models.Habit, habit_id)
    if not h:
        raise HTTPException(404, "习惯不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(h, k, v)
    db.commit()
    db.refresh(h)
    return h


@router.delete("/{habit_id}")
def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    h = db.get(models.Habit, habit_id)
    if not h:
        raise HTTPException(404, "习惯不存在")
    db.delete(h)
    db.commit()
    return {"ok": True}


@router.post("/{habit_id}/log", response_model=schemas.HabitLogOut)
def log_habit(habit_id: int, body: schemas.HabitLogCreate, db: Session = Depends(get_db)):
    h = db.get(models.Habit, habit_id)
    if not h:
        raise HTTPException(404, "习惯不存在")
    existing = (
        db.query(models.HabitLog)
        .filter(
            and_(models.HabitLog.habit_id == habit_id, models.HabitLog.logged_date == body.logged_date)
        )
        .first()
    )
    if existing:
        existing.completed = body.completed
        db.commit()
        db.refresh(existing)
        return existing
    log = models.HabitLog(habit_id=habit_id, logged_date=body.logged_date, completed=body.completed)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/{habit_id}/logs", response_model=list[schemas.HabitLogOut])
def list_habit_logs(habit_id: int, db: Session = Depends(get_db), limit: int = 90):
    h = db.get(models.Habit, habit_id)
    if not h:
        raise HTTPException(404, "习惯不存在")
    return (
        db.query(models.HabitLog)
        .filter(models.HabitLog.habit_id == habit_id)
        .order_by(models.HabitLog.logged_date.desc())
        .limit(min(limit, 365))
        .all()
    )
