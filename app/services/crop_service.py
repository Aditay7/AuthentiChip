import os
import cv2
import numpy as np
from datetime import datetime
from typing import Tuple, Dict, Optional

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.services.crop_dimensions.smart_crop import SmartCropper


class CropService:
    """Service for processing and cropping IC images using SmartCropper"""
    
    def __init__(self):
        self.settings = get_settings()
        self.upload_dir = self.settings.UPLOAD_DIR
        self.cropped_dir = os.path.join(self.upload_dir, "cropped")
        
        # Create cropped directory if it doesn't exist
        os.makedirs(self.cropped_dir, exist_ok=True)
        
        # Initialize SmartCropper
        self.cropper = SmartCropper(debug_mode=False)
    
    def process_scan_image(
        self, 
        scan_id: str, 
        original_image_path: str
    ) -> Tuple[str, Dict]:
        """
        Process a scan image using SmartCropper.
        
        Args:
            scan_id: MongoDB ObjectId of the scan
            original_image_path: Relative path to original image (e.g., "original/capture_20251208_103412.jpg")
            
        Returns:
            Tuple[str, Dict]: (cropped_image_path, processing_stats)
            
        Raises:
            HTTPException: If image file not found or processing fails
        """
        # Construct full path to original image
        full_original_path = os.path.join(self.upload_dir, original_image_path)
        
        # Check if original image exists
        if not os.path.exists(full_original_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Original image not found at {original_image_path}"
            )
        
        # Load image using OpenCV
        img = cv2.imread(full_original_path)
        
        if img is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load image from {original_image_path}"
            )
        
        # Process image using SmartCropper
        cropped_img, stats = self.cropper.process_image(img)
        
        if cropped_img is None:
            error_msg = stats.get("error", "Unknown error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Image processing failed: {error_msg}"
            )
        
        # Generate filename for cropped image
        # Extract timestamp from original filename or use current time
        original_filename = os.path.basename(original_image_path)
        if original_filename.startswith("capture_"):
            # Extract timestamp from original filename
            timestamp_part = original_filename.replace("capture_", "").replace(".jpg", "")
            cropped_filename = f"cropped_{timestamp_part}.jpg"
        else:
            # Use current timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cropped_filename = f"cropped_{timestamp}.jpg"
        
        # Create relative and full paths
        relative_cropped_path = os.path.join("cropped", cropped_filename)
        full_cropped_path = os.path.join(self.upload_dir, relative_cropped_path)
        
        # Save cropped image
        success = cv2.imwrite(full_cropped_path, cropped_img)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save cropped image to disk"
            )
        
        return relative_cropped_path, stats
