from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app import schemas

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[schemas.EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(models.CalendarEvent).order_by(models.CalendarEvent.start_at.asc()).limit(500).all()


@router.post("", response_model=schemas.EventOut)
def create_event(body: schemas.EventCreate, db: Session = Depends(get_db)):
    e = models.CalendarEvent(**body.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    e = db.get(models.CalendarEvent, event_id)
    if not e:
        raise HTTPException(404, "日程不存在")
    return e


@router.patch("/{event_id}", response_model=schemas.EventOut)
def update_event(event_id: int, body: schemas.EventUpdate, db: Session = Depends(get_db)):
    e = db.get(models.CalendarEvent, event_id)
    if not e:
        raise HTTPException(404, "日程不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(e, k, v)
    db.commit()
    db.refresh(e)
    return e


@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    e = db.get(models.CalendarEvent, event_id)
    if not e:
        raise HTTPException(404, "日程不存在")
    db.delete(e)
    db.commit()
    return {"ok": True}
