from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from backend.database import get_session
from backend.models import (
    CurveSet, CurveSetCreate, CurveSetRead, CurveSetReadWithSeries, CurveSetUpdate,
    CurveSeries, CurveSeriesCreate, CurveSeriesRead,
    CurvePoint, CurvePointCreate, SeriesType
)

router = APIRouter(prefix="/curve-sets", tags=["curve-sets"])

@router.post("/", response_model=CurveSetRead)
def create_curve_set(curve_set: CurveSetCreate, session: Session = Depends(get_session)):
    db_curve_set = CurveSet.model_validate(curve_set)
    session.add(db_curve_set)
    session.commit()
    session.refresh(db_curve_set)
    return db_curve_set

@router.get("/{curve_set_id}", response_model=CurveSetReadWithSeries)
def read_curve_set(curve_set_id: int, session: Session = Depends(get_session)):
    curve_set = session.get(CurveSet, curve_set_id)
    if not curve_set:
        raise HTTPException(status_code=404, detail="Curve Set not found")
    return curve_set

@router.patch("/{curve_set_id}", response_model=CurveSetRead)
def update_curve_set(curve_set_id: int, curve_set_update: CurveSetUpdate, session: Session = Depends(get_session)):
    db_curve_set = session.get(CurveSet, curve_set_id)
    if not db_curve_set:
        raise HTTPException(status_code=404, detail="Curve Set not found")

    curve_set_data = curve_set_update.model_dump(exclude_unset=True)
    db_curve_set.sqlmodel_update(curve_set_data)
    session.add(db_curve_set)
    session.commit()
    session.refresh(db_curve_set)
    return db_curve_set

@router.delete("/{curve_set_id}")
def delete_curve_set(curve_set_id: int, session: Session = Depends(get_session)):
    curve_set = session.get(CurveSet, curve_set_id)
    if not curve_set:
        raise HTTPException(status_code=404, detail="Curve Set not found")
    session.delete(curve_set)
    session.commit()
    return {"ok": True}

# Series management

@router.post("/{curve_set_id}/series", response_model=CurveSeriesRead)
def create_curve_series(
    curve_set_id: int,
    series_data: CurveSeriesCreate,
    session: Session = Depends(get_session)
):
    curve_set = session.get(CurveSet, curve_set_id)
    if not curve_set:
        raise HTTPException(status_code=404, detail="Curve Set not found")

    if series_data.curve_set_id != curve_set_id:
         raise HTTPException(status_code=400, detail="Curve Set ID mismatch")

    # Check if series of this type already exists? Requirement says "Multiple series types must be supported".
    # Usually one head curve per set, but maybe duplicates allowed? Let's assume unique type per set for now or allow multiple.
    # Requirement: "Missing series (e.g. no efficiency curve provided)" implies existence check.
    # Let's check if type exists and overwrite or append?
    # Ideally, we allow only one series of each type per CurveSet for simplicity, or handle multiple.
    # Let's enforce uniqueness of type per curve set for now to keep it simple.

    existing_series = session.exec(
        select(CurveSeries)
        .where(CurveSeries.curve_set_id == curve_set_id)
        .where(CurveSeries.type == series_data.type)
    ).first()

    if existing_series:
        # Delete existing to replace? Or error?
        # Let's replace.
        session.delete(existing_series)
        session.commit()

    db_series = CurveSeries(curve_set_id=curve_set_id, type=series_data.type)
    session.add(db_series)
    session.commit()
    session.refresh(db_series)

    # Add points
    for pt in series_data.points:
        db_point = CurvePoint(
            series_id=db_series.id,
            flow=pt.flow,
            value=pt.value,
            sequence=pt.sequence
        )
        session.add(db_point)

    session.commit()
    session.refresh(db_series)
    return db_series

@router.delete("/series/{series_id}")
def delete_curve_series(series_id: int, session: Session = Depends(get_session)):
    series = session.get(CurveSeries, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    session.delete(series)
    session.commit()
    return {"ok": True}
