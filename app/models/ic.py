from typing import List, Optional
from pydantic import BaseModel, Field


class PackageDimensions(BaseModel):
    length_min_mm: Optional[float] = None
    length_nom_mm: Optional[float] = None
    length_max_mm: Optional[float] = None
    breadth_min_mm: Optional[float] = None
    breadth_nom_mm: Optional[float] = None
    breadth_max_mm: Optional[float] = None


class ModelResult(BaseModel):
    passed: bool = False
    score: Optional[float] = None



class ICRecordBase(BaseModel):
    manufacturer: str
    base_part_number: str

    full_part_numbers: List[str] = Field(default_factory=list)
    allowed_markings: List[str] = Field(default_factory=list)

    package_type: str
    pin_count: Optional[int] = None

    package_dimensions: Optional[PackageDimensions] = None

    model_1: ModelResult = Field(default_factory=ModelResult)
    model_2: ModelResult = Field(default_factory=ModelResult)
    model_3: ModelResult = Field(default_factory=ModelResult)
    model_4: ModelResult = Field(default_factory=ModelResult)

    confidence_score: int = 0
    datecode_pattern: Optional[str] = None


class ICRecordCreate(ICRecordBase):
    """Used for request body while creating new record"""
    pass


class ICRecordUpdate(BaseModel):
    """Used for partial updates via PATCH endpoint"""
    manufacturer: Optional[str] = None
    base_part_number: Optional[str] = None
    full_part_numbers: Optional[List[str]] = None
    allowed_markings: Optional[List[str]] = None
    package_type: Optional[str] = None
    pin_count: Optional[int] = None
    package_dimensions: Optional[PackageDimensions] = None
    model_1: Optional[ModelResult] = None
    model_2: Optional[ModelResult] = None
    model_3: Optional[ModelResult] = None
    model_4: Optional[ModelResult] = None
    confidence_score: Optional[int] = None
    datecode_pattern: Optional[str] = None


class ICRecordOut(ICRecordBase):
    """Used for response output"""
    id: str
