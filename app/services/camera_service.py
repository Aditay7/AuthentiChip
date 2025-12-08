import os
from datetime import datetime
from typing import Tuple

import requests
from fastapi import HTTPException, status

from app.core.config import get_settings


class CameraService:
    """Service for handling Raspberry Pi camera capture operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.pi_capture_url = self.settings.PI_CAPTURE_URL
        self.upload_dir = os.path.join(self.settings.UPLOAD_DIR, "original")
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def capture_from_pi(self) -> bytes:
        """
        Call Raspberry Pi /capture endpoint and return JPEG bytes.
        
        Returns:
            bytes: Raw JPEG image data
            
        Raises:
            HTTPException: If Pi is unreachable or returns error
        """
        try:
            # Call Raspberry Pi capture endpoint with timeout
            response = requests.get(self.pi_capture_url, timeout=10)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Pi capture failed with status {response.status_code}"
                )
            
            # Get raw JPEG bytes
            img_bytes = response.content
            
            if not img_bytes:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Empty image received from Pi"
                )
            
            return img_bytes
            
        except requests.exceptions.Timeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Raspberry Pi camera timeout - check if device is online"
            )
        except requests.exceptions.ConnectionError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot reach Raspberry Pi at {self.pi_capture_url}"
            )
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error communicating with Raspberry Pi: {str(e)}"
            )
    
    def save_image_to_disk(self, img_bytes: bytes) -> str:
        """
        Save image bytes to disk with timestamp filename.
        
        Args:
            img_bytes: Raw JPEG image data
            
        Returns:
            str: Relative file path where image was saved
        """
        # Generate timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.jpg"
        
        # Create relative path
        relative_path = os.path.join("original", filename)
        full_path = os.path.join(self.settings.UPLOAD_DIR, relative_path)
        
        # Save image to disk
        with open(full_path, "wb") as f:
            f.write(img_bytes)
        
        return relative_path
    
    def capture_and_save(self) -> Tuple[str, bytes]:
        """
        Capture image from Pi and save to disk.
        
        Returns:
            Tuple[str, bytes]: (file_path, image_bytes)
        """
        img_bytes = self.capture_from_pi()
        file_path = self.save_image_to_disk(img_bytes)
        return file_path, img_bytes
    
    def save_uploaded_file(self, file_bytes: bytes, filename: str) -> str:
        """
        Save uploaded file to disk with timestamp filename.
        
        Args:
            file_bytes: Raw image file bytes
            filename: Original filename (used for extension)
            
        Returns:
            str: Relative file path where image was saved
            
        Raises:
            HTTPException: If file save fails
        """
        # Generate timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get file extension from original filename
        file_ext = os.path.splitext(filename)[1].lower()
        if not file_ext:
            file_ext = '.jpg'  # Default to jpg if no extension
        
        new_filename = f"upload_{timestamp}{file_ext}"
        
        # Create relative path
        relative_path = os.path.join("original", new_filename)
        full_path = os.path.join(self.settings.UPLOAD_DIR, relative_path)
        
        # Save image to disk
        try:
            with open(full_path, "wb") as f:
                f.write(file_bytes)
            return relative_path
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save uploaded image: {str(e)}"
            )
