# app/models/scan.py

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---- ENUMS -----------------------------------------------------------------


class ScanStatus(str, Enum):
    """Lifecycle of a scan."""
    PENDING = "pending"         # uploaded, waiting for model
    PROCESSED = "processed"     # model + rules finished, decision stored
    FLAGGED = "flagged"         # auto-flagged by rules (red / yellow)
    DISPUTED = "disputed"       # human has raised a dispute


# ---- BASE SCHEMA (common fields) -------------------------------------------


class ScanBase(BaseModel):
    """
    Common fields for a Scan.
    Text comes from your image-recognition model, NOT a separate OCR.
    """

    device_id: Optional[str] = Field(
        default=None,
        description="ID of edge device that captured the image (if any).",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Worker/operator user id (if scan initiated from UI).",
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the scan was created (UTC).",
    )

    # Optional: part number if the operator knows it when scanning
    part_number: Optional[str] = Field(
        default=None,
        description="Expected part number, if known at scan time.",
    )

    # Paths / URLs to stored images (original + maybe cropped)
    images: List[str] = Field(
        default_factory=list,
        description="List of image paths/URLs stored on disk/object storage.",
    )

    # Output of your image-recognition model:
    recognized_text: Optional[str] = Field(
        default=None,
        description="Text predicted from IC image by the recognition model.",
    )
    recognition_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extra info: confidences, per-character scores, bounding boxes, etc.",
    )

    # Anomalies / authenticity
    anomalies: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of detected anomalies (logo mismatch, surface defects, etc.).",
    )
    authenticity_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="0–1 score (higher = more likely authentic).",
    )

    # Comparison against datasheet / rules (will fill later)
    datasheet_refs: List[str] = Field(
        default_factory=list,
        description="IDs/links of datasheets or templates used for comparison.",
    )
    comparison_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured result of rule engine (decision, reasons, thresholds).",
    )

    status: ScanStatus = Field(
        default=ScanStatus.PENDING,
        description="Current status of the scan.",
    )

    # Free-form comments (disputes, notes)
    comments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Comments like {user_id, text, at}.",
    )


# ---- CREATE / UPDATE / DB MODELS -------------------------------------------


class ScanCreate(ScanBase):
    """
    Data required when creating a scan record.
    For the upload endpoint, you'll mostly fill:
      - device_id / user_id
      - part_number (optional)
      - images (paths after saving files)
    Model outputs will be added later during processing.
    """

    # For creation we at least need one stored image path:
    images: List[str] = Field(..., min_items=1)


class ScanUpdate(BaseModel):
    """
    Partial updates used after model inference & rules engine.
    Everything is optional so you can PATCH specific fields.
    """

    recognized_text: Optional[str] = None
    recognition_metadata: Optional[Dict[str, Any]] = None
    anomalies: Optional[List[Dict[str, Any]]] = None
    authenticity_score: Optional[float] = Field(default=None, ge=0, le=1)
    datasheet_refs: Optional[List[str]] = None
    comparison_result: Optional[Dict[str, Any]] = None
    status: Optional[ScanStatus] = None
    comments: Optional[List[Dict[str, Any]]] = None


class ScanInDB(ScanBase):
    """
    Representation stored in MongoDB.
    `_id` is aliased to `id` so you can work with `id` in Python while
    Mongo still stores `_id` in the collection.
    """

    id: str = Field(default_factory=str, alias="_id")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
