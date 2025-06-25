from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app import crud

router = APIRouter(tags=["feature-updates"])

@router.get("/api/v1/feature-updates/today")
def get_today_update(db: Session = Depends(get_db)):
    obj = crud.get_today_update(db)
    return {"date": date.today().isoformat(), "update": obj.content if obj else ""}

@router.get("/api/v1/feature-updates/history")
def get_update_history(db: Session = Depends(get_db)):
    objs = crud.get_update_history(db)
    return [{"date": o.date.isoformat(), "content": o.content} for o in objs]

@router.post("/api/v1/feature-updates/update")
def upsert_update(content: str, target_date: str = None, db: Session = Depends(get_db)):
    from datetime import date as dtdate
    d = dtdate.fromisoformat(target_date) if target_date else date.today()
    obj = crud.upsert_update(db, d, content)
    return {"date": obj.date.isoformat(), "content": obj.content} 