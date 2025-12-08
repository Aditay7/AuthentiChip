from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.client import get_database
from app.repositories.scan_repository import ScanRepository
from app.services.camera_service import CameraService
from app.services.crop_service import CropService

router = APIRouter(prefix="/scan", tags=["scan"])


def get_scan_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> ScanRepository:
    """Dependency to get Scan repository instance"""
    return ScanRepository(db)


def get_camera_service() -> CameraService:
    """Dependency to get Camera service instance"""
    return CameraService()


def get_crop_service() -> CropService:
    """Dependency to get Crop service instance"""
    return CropService()


@router.post("/capture")
async def capture_from_camera(
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    repo: ScanRepository = Depends(get_scan_repository),
    camera: CameraService = Depends(get_camera_service)
) -> dict:
    """
    Capture image from Raspberry Pi camera and create scan record.
    
    This endpoint:
    1. Calls the Raspberry Pi /capture endpoint to get a JPEG image
    2. Saves the image to disk with a timestamp-based filename
    3. Creates a new scan document in MongoDB with minimal required fields
    4. Returns the MongoDB ObjectId of the created scan
    
    Query Parameters:
        user_id: Optional MongoDB ObjectId of the user performing the scan
        username: Optional username of the user performing the scan
    
    Returns:
        dict: {
            "scan_id": "<MongoDB ObjectId>",
            "image_path": "scans/capture_YYYYMMDD_HHMMSS.jpg",
            "message": "Image captured and scan created successfully"
        }
    
    Raises:
        502: Pi capture failed
        503: Cannot reach Raspberry Pi
        504: Pi timeout
        500: Internal server error
    """
    try:
        # Step 1: Capture image from Pi and save to disk
        image_path, img_bytes = camera.capture_and_save()
        
        # Step 2: Create scan document with minimal required fields
        scan_data = {
            # User tracking (optional)
            "user_id": user_id,
            "username": username,
            
            # Timestamps
            "scanned_at": datetime.utcnow(),
            "updated_at": None,
            
            # IC Information (minimal defaults - will be filled later)
            "manufacturer": "Unknown",
            "full_part_number": "Unknown",
            "allowed_markings": [],
            "package_type": "Unknown",
            
            # Dimensions and Images
            "package_dimensions": None,
            "image_data": {
                "original_image_path": image_path,
                "cropped_image_path": None,
                "content_type": "image/jpeg"
            },
            
            # Verification Results (defaults)
            "dimensions_match": False,
            "texture_model_confidence_score": 0,
            "overall_confidence_score": 0,
            
            # Notes
            "notes": "Image captured from Raspberry Pi camera"
        }
        
        # Step 3: Save to database
        created = await repo.create(scan_data)
        scan_id = str(created["_id"])
        
        # Step 4: Return response
        return {
            "scan_id": scan_id,
            "image_path": image_path,
            "message": "Image captured and scan created successfully"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions from camera service
        raise
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to capture and save scan: {str(e)}"
        )


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    repo: ScanRepository = Depends(get_scan_repository),
    camera: CameraService = Depends(get_camera_service)
) -> dict:
    """
    Upload an image file and create scan record.
    
    This endpoint:
    1. Accepts an image file upload via multipart/form-data
    2. Validates file type (JPG, JPEG, PNG only)
    3. Validates file size (max 10MB)
    4. Saves the image to disk with a timestamp-based filename
    5. Creates a new scan document in MongoDB
    6. Returns the MongoDB ObjectId of the created scan
    
    Form Data:
        file: Image file (JPG, JPEG, PNG)
        
    Query Parameters:
        user_id: Optional MongoDB ObjectId of the user performing the scan
        username: Optional username of the user performing the scan
    
    Returns:
        dict: {
            "scan_id": "<MongoDB ObjectId>",
            "image_path": "original/upload_YYYYMMDD_HHMMSS.jpg",
            "message": "Image uploaded and scan created successfully"
        }
    
    Raises:
        400: No file provided or invalid file type
        413: File size exceeds limit
        500: Internal server error
    """
    try:
        # Step 1: Validate file is provided
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file uploaded"
            )
        
        # Step 2: Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPG, JPEG, PNG allowed"
            )
        
        # Step 3: Read file content
        file_bytes = await file.read()
        
        # Step 4: Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if len(file_bytes) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 10MB limit"
            )
        
        # Step 5: Save uploaded file to disk
        image_path = camera.save_uploaded_file(file_bytes, file.filename)
        
        # Step 6: Create scan document with minimal required fields
        scan_data = {
            # User tracking (optional)
            "user_id": user_id,
            "username": username,
            
            # Timestamps
            "scanned_at": datetime.utcnow(),
            "updated_at": None,
            
            # IC Information (minimal defaults - will be filled later)
            "manufacturer": "Unknown",
            "full_part_number": "Unknown",
            "allowed_markings": [],
            "package_type": "Unknown",
            
            # Dimensions and Images
            "package_dimensions": None,
            "image_data": {
                "original_image_path": image_path,
                "cropped_image_path": None,
                "content_type": file.content_type
            },
            
            # Verification Results (defaults)
            "dimensions_match": False,
            "texture_model_confidence_score": 0,
            "overall_confidence_score": 0,
            
            # Notes
            "notes": "Image uploaded from frontend"
        }
        
        # Step 7: Save to database
        created = await repo.create(scan_data)
        scan_id = str(created["_id"])
        
        # Step 8: Return response
        return {
            "scan_id": scan_id,
            "image_path": image_path,
            "message": "Image uploaded and scan created successfully"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload and save scan: {str(e)}"
        )


@router.post("/{scan_id}/process")
async def process_scan_image(
    scan_id: str,
    repo: ScanRepository = Depends(get_scan_repository),
    crop_service: CropService = Depends(get_crop_service)
) -> dict:
    """
    Process a captured scan image using SmartCropper.
    
    This endpoint:
    1. Retrieves the scan document by scan_id
    2. Gets the original_image_path from the scan
    3. Processes the image through SmartCropper (detects IC, rotates, crops)
    4. Saves the cropped image to uploads/cropped/
    5. Updates the scan document with cropped_image_path
    6. Returns the updated scan with both image paths and processing stats
    
    Path Parameters:
        scan_id: MongoDB ObjectId of the scan (from /capture response)
    
    Returns:
        dict: {
            "scan_id": "<ObjectId>",
            "original_image_path": "original/capture_20251208_103412.jpg",
            "cropped_image_path": "cropped/cropped_20251208_103412.jpg",
            "processing_stats": {
                "width": 512.5,
                "height": 384.2,
                "angle": 2.3,
                "original_width": 520.0,
                "original_height": 390.0
            },
            "message": "Image processed successfully"
        }
    
    Raises:
        404: Scan not found or original image not found
        400: Scan doesn't have original image path
        500: Image processing failed
    """
    try:
        # Step 1: Retrieve scan document
        scan = await repo.get_by_id(scan_id)
        
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan with id {scan_id} not found"
            )
        
        # Step 2: Get original image path
        image_data = scan.get("image_data", {})
        original_image_path = image_data.get("original_image_path")
        
        if not original_image_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scan does not have an original image path"
            )
        
        # Step 3: Process image using CropService
        cropped_image_path, processing_stats = crop_service.process_scan_image(
            scan_id=scan_id,
            original_image_path=original_image_path
        )
        
        # Step 4: Update scan document with cropped image path
        update_data = {
            "image_data.cropped_image_path": cropped_image_path,
            "updated_at": datetime.utcnow()
        }
        
        updated_scan = await repo.update(scan_id, update_data)
        
        if not updated_scan:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update scan document"
            )
        
        # Step 5: Return response
        return {
            "scan_id": scan_id,
            "original_image_path": original_image_path,
            "cropped_image_path": cropped_image_path,
            "message": "Image processed successfully"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process scan image: {str(e)}"
        )

