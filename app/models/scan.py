from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Reuse IC database models for consistency
from app.models.ic_database import PackageDimensions, ICImageData


class ScanBase(BaseModel):
    """
    Scan model - combines IC database fields with user tracking.
    Used when workers scan ICs for verification.
    """
    # User tracking (can be null for public/non-authenticated scans)
    user_id: Optional[str] = Field(
        default=None,
        description="MongoDB ObjectId of the worker/user who performed the scan"
    )
    username: Optional[str] = Field(
        default=None,
        description="Username of the worker who performed the scan"
    )
    
    # Timestamps
    scanned_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the scan was performed (UTC)"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp (UTC)"
    )
    
    # IC Information (same as ic_database)
    manufacturer: str
    full_part_number: str
    allowed_markings: List[str] = Field(default_factory=list)
    package_type: str
    
    # Dimensions and Images
    package_dimensions: Optional[PackageDimensions] = None
    image_data: Optional[ICImageData] = None
    
    # Verification Results
    dimensions_match: bool = False
    texture_model_confidence_score: int = 0
    overall_confidence_score: int = 0
    
    
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes or comments about the scan"
    )


class ScanCreate(ScanBase):
    """Used for creating new scan records"""
    pass


class ScanUpdate(BaseModel):
    """Used for partial updates via PATCH endpoint"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    manufacturer: Optional[str] = None
    full_part_number: Optional[str] = None
    allowed_markings: Optional[List[str]] = None
    package_type: Optional[str] = None
    
    package_dimensions: Optional[PackageDimensions] = None
    image_data: Optional[ICImageData] = None
    
    dimensions_match: Optional[bool] = None
    texture_model_confidence_score: Optional[int] = None
    overall_confidence_score: Optional[int] = None

    notes: Optional[str] = None


class ScanOut(ScanBase):
    """Used for response output"""
    id: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
