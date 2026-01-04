from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from backend.database import get_session
from backend.models import Pump, PumpCreate, PumpRead, PumpReadWithCurveSets, PumpUpdate, Organization, UserRole, CurveSet, CurveSetRead
from backend.dependencies import get_active_org, RequireRole
from datetime import datetime

router = APIRouter(prefix="/pumps", tags=["pumps"])

@router.post("/", response_model=PumpRead)
def create_pump(
    pump: PumpCreate,
    session: Session = Depends(get_session),
    org: Organization = Depends(get_active_org),
    role: UserRole = Depends(RequireRole({UserRole.editor, UserRole.admin}))
):
    # Using model_validate instead of from_orm
    # And specifically setting org_id before validation might be tricky if it's strict,
    # but SQLModel usually allows extra if strict is False.
    # However, org_id is required in Pump, but not in PumpCreate.
    # So we should convert PumpCreate to dict, add org_id, then validate.

    data = pump.model_dump()
    data["org_id"] = org.id
    db_pump = Pump.model_validate(data)

    session.add(db_pump)
    session.commit()
    session.refresh(db_pump)
    return db_pump

@router.get("/", response_model=List[PumpRead])
def read_pumps(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    org: Organization = Depends(get_active_org)
):
    pumps = session.exec(
        select(Pump)
        .where(Pump.org_id == org.id)
        .offset(skip)
        .limit(limit)
    ).all()
    return pumps

@router.get("/{pump_id}", response_model=PumpReadWithCurveSets)
def read_pump(
    pump_id: int,
    session: Session = Depends(get_session),
    org: Organization = Depends(get_active_org)
):
    pump = session.get(Pump, pump_id)
    if not pump or pump.org_id != org.id:
        raise HTTPException(status_code=404, detail="Pump not found")
    return pump

@router.patch("/{pump_id}", response_model=PumpRead)
def update_pump(
    pump_id: int,
    pump_update: PumpUpdate,
    session: Session = Depends(get_session),
    org: Organization = Depends(get_active_org),
    role: UserRole = Depends(RequireRole({UserRole.editor, UserRole.admin}))
):
    db_pump = session.get(Pump, pump_id)
    if not db_pump or db_pump.org_id != org.id:
        raise HTTPException(status_code=404, detail="Pump not found")

    pump_data = pump_update.model_dump(exclude_unset=True)
    for key, value in pump_data.items():
        setattr(db_pump, key, value)

    db_pump.updated_at = datetime.utcnow()
    session.add(db_pump)
    session.commit()
    session.refresh(db_pump)
    return db_pump

@router.delete("/{pump_id}")
def delete_pump(
    pump_id: int,
    session: Session = Depends(get_session),
    org: Organization = Depends(get_active_org),
    role: UserRole = Depends(RequireRole({UserRole.editor, UserRole.admin}))
):
    db_pump = session.get(Pump, pump_id)
    if not db_pump or db_pump.org_id != org.id:
        raise HTTPException(status_code=404, detail="Pump not found")

    session.delete(db_pump)
    session.commit()
    return {"ok": True}
