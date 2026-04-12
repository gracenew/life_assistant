from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app import schemas

router = APIRouter(prefix="/api/transactions", tags=["finance"])


@router.get("", response_model=list[schemas.TransactionOut])
def list_transactions(db: Session = Depends(get_db), limit: int = 200):
    return (
        db.query(models.Transaction)
        .order_by(models.Transaction.occurred_at.desc())
        .limit(min(limit, 500))
        .all()
    )


@router.post("", response_model=schemas.TransactionOut)
def create_transaction(body: schemas.TransactionCreate, db: Session = Depends(get_db)):
    t = models.Transaction(**body.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get("/{tx_id}", response_model=schemas.TransactionOut)
def get_transaction(tx_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Transaction, tx_id)
    if not t:
        raise HTTPException(404, "记录不存在")
    return t


@router.patch("/{tx_id}", response_model=schemas.TransactionOut)
def update_transaction(tx_id: int, body: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    t = db.get(models.Transaction, tx_id)
    if not t:
        raise HTTPException(404, "记录不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{tx_id}")
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Transaction, tx_id)
    if not t:
        raise HTTPException(404, "记录不存在")
    db.delete(t)
    db.commit()
    return {"ok": True}
