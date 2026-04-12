from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app import schemas

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[schemas.TaskOut])
def list_tasks(db: Session = Depends(get_db), status: Optional[str] = None):
    q = db.query(models.Task).order_by(models.Task.due_at.asc().nulls_last(), models.Task.id.desc())
    if status:
        q = q.filter(models.Task.status == status)
    return q.limit(200).all()


@router.post("", response_model=schemas.TaskOut)
def create_task(body: schemas.TaskCreate, db: Session = Depends(get_db)):
    t = models.Task(**body.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Task, task_id)
    if not t:
        raise HTTPException(404, "任务不存在")
    return t


@router.patch("/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, body: schemas.TaskUpdate, db: Session = Depends(get_db)):
    t = db.get(models.Task, task_id)
    if not t:
        raise HTTPException(404, "任务不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    t.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Task, task_id)
    if not t:
        raise HTTPException(404, "任务不存在")
    db.delete(t)
    db.commit()
    return {"ok": True}
