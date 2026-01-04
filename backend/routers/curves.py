from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
from backend.database import get_session
from backend.models import (
    CurveSet, CurveSetCreate, CurveSetRead, CurveSetReadWithSeries, CurveSetUpdate,
    CurveSeries, CurveSeriesCreate, CurveSeriesRead,
    CurvePoint, CurvePointCreate, SeriesType
)
from backend.curves.validation import validate_points, ValidationResult
from backend.curves.fitting import fit_curve
from backend.curves.evaluation import evaluate_curve_at_point

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

# Validation Endpoint

@router.post("/validate", response_model=ValidationResult)
def validate_curve_points(
    curve_type: SeriesType = Body(...),
    points: List[Dict[str, Any]] = Body(...)
):
    """
    Validates curve points without saving.
    """
    return validate_points(curve_type, points)

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

    # 1. Validate Points
    raw_points = [p.model_dump() for p in series_data.points]
    validation_res = validate_points(series_data.type, raw_points)

    if validation_res.blocking_errors:
        raise HTTPException(status_code=400, detail={"message": "Validation failed", "errors": validation_res.blocking_errors})

    # Use normalized points
    normalized_points = validation_res.normalized_points

    # 2. Check for existing series
    existing_series = session.exec(
        select(CurveSeries)
        .where(CurveSeries.curve_set_id == curve_set_id)
        .where(CurveSeries.type == series_data.type)
    ).first()

    if existing_series:
        session.delete(existing_series)
        session.commit()

    # 3. Fit Curve
    fit_model_type, fit_params, fit_quality, data_range = fit_curve(series_data.type, normalized_points)

    # 4. Create Series
    db_series = CurveSeries(
        curve_set_id=curve_set_id,
        type=series_data.type,
        validation_warnings=validation_res.warnings,
        fit_model_type=fit_model_type,
        fit_params=fit_params,
        fit_quality=fit_quality,
        data_range=data_range
    )
    session.add(db_series)
    session.commit()
    session.refresh(db_series)

    # Add points
    for i, pt in enumerate(normalized_points):
        db_point = CurvePoint(
            series_id=db_series.id,
            flow=pt["flow"],
            value=pt["value"],
            sequence=i
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

# Fit and Evaluation Endpoints

@router.post("/series/{series_id}/fit")
def fit_series(series_id: int, session: Session = Depends(get_session)):
    """
    Manually re-fit a series.
    """
    series = session.get(CurveSeries, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # Get points
    points = [{"flow": p.flow, "value": p.value} for p in series.points]

    fit_model_type, fit_params, fit_quality, data_range = fit_curve(series.type, points)

    series.fit_model_type = fit_model_type
    series.fit_params = fit_params
    series.fit_quality = fit_quality
    series.data_range = data_range

    session.add(series)
    session.commit()
    session.refresh(series)

    return {
        "fit_model_type": fit_model_type,
        "fit_params": fit_params,
        "fit_quality": fit_quality,
        "data_range": data_range
    }

@router.post("/series/{series_id}/evaluate")
def evaluate_series(
    series_id: int,
    flow: float = Body(..., embed=True),
    head_optional: Optional[float] = Body(None, embed=True),
    session: Session = Depends(get_session)
):
    series = session.get(CurveSeries, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    points = [{"flow": p.flow, "value": p.value} for p in series.points]

    result = evaluate_curve_at_point(
        series.fit_model_type,
        series.fit_params,
        series.data_range or {}, # Handle None
        flow,
        points
    )

    response = {
        "predictions": {},
        "extrapolation": result["is_extrapolation"],
        "warnings": result["warnings"],
        "residuals": None
    }

    # Store prediction in the appropriate field based on series type
    response["predictions"][series.type.value] = result["predicted_value"]

    # Duty point check (specifically for Head)
    if head_optional is not None and series.type == SeriesType.head and result["predicted_value"] is not None:
         pred = result["predicted_value"]
         residual = head_optional - pred
         response["residuals"] = {
             "value": residual,
             "pass": abs(residual) <= 0.05 * pred # Default 5% tolerance
         }

    return response
