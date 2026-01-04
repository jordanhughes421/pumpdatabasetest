from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from enum import Enum

class SeriesType(str, Enum):
    head = "head"
    efficiency = "efficiency"
    power = "power"

# Base Models

class PumpBase(SQLModel):
    manufacturer: str = Field(index=True)
    model: str = Field(index=True)
    meta_data: Optional[Dict[str, Any]] = Field(default={}, sa_column=Column(JSON))

class CurveSetBase(SQLModel):
    name: str
    pump_id: int = Field(foreign_key="pump.id")
    units: Dict[str, str] = Field(default={}, sa_column=Column(JSON)) # e.g. {"flow": "gpm", "head": "ft"}
    meta_data: Optional[Dict[str, Any]] = Field(default={}, sa_column=Column(JSON))

class CurveSeriesBase(SQLModel):
    curve_set_id: int = Field(foreign_key="curveset.id")
    type: SeriesType

class CurvePointBase(SQLModel):
    series_id: int = Field(foreign_key="curveseries.id")
    flow: float
    value: float
    sequence: int = 0

# Database Models

class Pump(PumpBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    curve_sets: List["CurveSet"] = Relationship(back_populates="pump", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class CurveSet(CurveSetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    pump: Optional[Pump] = Relationship(back_populates="curve_sets")
    series: List["CurveSeries"] = Relationship(back_populates="curve_set", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class CurveSeries(CurveSeriesBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # New fields for Validation and Fitting
    validation_warnings: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    fit_model_type: Optional[str] = None
    fit_params: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    fit_quality: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    data_range: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    curve_set: Optional[CurveSet] = Relationship(back_populates="series")
    points: List["CurvePoint"] = Relationship(back_populates="series", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class CurvePoint(CurvePointBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    series: Optional[CurveSeries] = Relationship(back_populates="points")

# Pydantic Schemas for API

class CurvePointInput(SQLModel):
    flow: float
    value: float
    sequence: int = 0

class CurvePointCreate(CurvePointBase):
    pass

class CurvePointRead(CurvePointBase):
    id: int

class CurveSeriesCreate(CurveSeriesBase):
    points: List[CurvePointInput] = []

class CurveSeriesRead(CurveSeriesBase):
    id: int
    points: List[CurvePointRead] = []

    # Include new fields in response
    validation_warnings: List[Dict[str, Any]] = []
    fit_model_type: Optional[str] = None
    fit_params: Optional[Dict[str, Any]] = None
    fit_quality: Optional[Dict[str, Any]] = None
    data_range: Optional[Dict[str, Any]] = None

class CurveSetCreate(CurveSetBase):
    pass

class CurveSetRead(CurveSetBase):
    id: int
    created_at: datetime
    updated_at: datetime

class CurveSetReadWithSeries(CurveSetRead):
    series: List[CurveSeriesRead] = []

class CurveSetUpdate(SQLModel):
    name: Optional[str] = None
    units: Optional[Dict[str, str]] = None
    meta_data: Optional[Dict[str, Any]] = None

class PumpCreate(PumpBase):
    pass

class PumpRead(PumpBase):
    id: int
    created_at: datetime
    updated_at: datetime

class PumpReadWithCurveSets(PumpRead):
    curve_sets: List[CurveSetRead] = []

class PumpUpdate(SQLModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
