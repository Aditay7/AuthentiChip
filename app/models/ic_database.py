from typing import List, Optional
from pydantic import BaseModel, Field


class PackageDimensions(BaseModel):
    body_length_min_mm: Optional[float] = None
    body_length_nom_mm: Optional[float] = None
    body_length_max_mm: Optional[float] = None
    body_width_min_mm: Optional[float] = None
    body_width_nom_mm: Optional[float] = None
    body_width_max_mm: Optional[float] = None


class ICImageData(BaseModel):
    """Model for storing IC image file paths"""
    original_image_path: Optional[str] = None
    cropped_image_path: Optional[str] = None
    content_type: str = "image/jpeg"
    
    class Config:
        populate_by_name = True




class ICRecordBase(BaseModel):
    manufacturer: str
    full_part_number: str
    allowed_markings: List[str] = Field(default_factory=list)

    package_type: str

    package_dimensions: Optional[PackageDimensions] = None
    image_data: Optional[ICImageData] = None

class ICRecordCreate(ICRecordBase):
    """Used for request body while creating new record"""
    pass


class ICRecordUpdate(BaseModel):
    """Used for partial updates via PATCH endpoint"""
    manufacturer: Optional[str] = None
    full_part_number: Optional[str] = None
    allowed_markings: Optional[List[str]] = None
    package_type: Optional[str] = None
    package_dimensions: Optional[PackageDimensions] = None
    image_data: Optional[ICImageData] = None


class ICRecordOut(ICRecordBase):
    """Used for response output"""
    id: str
