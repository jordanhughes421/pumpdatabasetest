from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from backend.database import get_session
from backend.models import (
    Pump, PumpCreate, PumpRead, PumpReadWithCurveSets, PumpUpdate,
    CurveSet
)

router = APIRouter(prefix="/pumps", tags=["pumps"])

@router.post("/", response_model=PumpRead)
def create_pump(pump: PumpCreate, session: Session = Depends(get_session)):
    db_pump = Pump.model_validate(pump)
    session.add(db_pump)
    session.commit()
    session.refresh(db_pump)
    return db_pump

@router.get("/", response_model=List[PumpRead])
def read_pumps(
    skip: int = 0,
    limit: int = 100,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    session: Session = Depends(get_session)
):
    query = select(Pump)
    if manufacturer:
        query = query.where(Pump.manufacturer.contains(manufacturer))
    if model:
        query = query.where(Pump.model.contains(model))

    query = query.offset(skip).limit(limit)
    pumps = session.exec(query).all()
    return pumps

@router.get("/{pump_id}", response_model=PumpReadWithCurveSets)
def read_pump(pump_id: int, session: Session = Depends(get_session)):
    pump = session.get(Pump, pump_id)
    if not pump:
        raise HTTPException(status_code=404, detail="Pump not found")
    return pump

@router.patch("/{pump_id}", response_model=PumpRead)
def update_pump(pump_id: int, pump_update: PumpUpdate, session: Session = Depends(get_session)):
    db_pump = session.get(Pump, pump_id)
    if not db_pump:
        raise HTTPException(status_code=404, detail="Pump not found")

    pump_data = pump_update.model_dump(exclude_unset=True)
    db_pump.sqlmodel_update(pump_data)
    session.add(db_pump)
    session.commit()
    session.refresh(db_pump)
    return db_pump

@router.delete("/{pump_id}")
def delete_pump(pump_id: int, session: Session = Depends(get_session)):
    pump = session.get(Pump, pump_id)
    if not pump:
        raise HTTPException(status_code=404, detail="Pump not found")
    session.delete(pump)
    session.commit()
    return {"ok": True}
