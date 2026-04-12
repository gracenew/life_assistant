from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app import schemas

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("", response_model=list[schemas.NoteOut])
def list_notes(db: Session = Depends(get_db), q: Optional[str] = None):
    query = db.query(models.Note).order_by(models.Note.updated_at.desc())
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(models.Note.title.ilike(like), models.Note.body.ilike(like), models.Note.tags.ilike(like))
        )
    return query.limit(200).all()


@router.post("", response_model=schemas.NoteOut)
def create_note(body: schemas.NoteCreate, db: Session = Depends(get_db)):
    n = models.Note(**body.model_dump())
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


@router.get("/{note_id}", response_model=schemas.NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db)):
    n = db.get(models.Note, note_id)
    if not n:
        raise HTTPException(404, "笔记不存在")
    return n


@router.patch("/{note_id}", response_model=schemas.NoteOut)
def update_note(note_id: int, body: schemas.NoteUpdate, db: Session = Depends(get_db)):
    n = db.get(models.Note, note_id)
    if not n:
        raise HTTPException(404, "笔记不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(n, k, v)
    n.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(n)
    return n


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    n = db.get(models.Note, note_id)
    if not n:
        raise HTTPException(404, "笔记不存在")
    db.delete(n)
    db.commit()
    return {"ok": True}
