"""
IC Datasheet Extraction API Router

Provides REST API endpoints for extracting IC dimensions from datasheets.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.web_scapper.web_scrapper import (
    scrape_and_extract,
    extract_dimensions_with_gemini,
    download_pdf
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/extract", tags=["IC Extraction"])

# Thread pool for blocking operations (limit concurrency)
executor = ThreadPoolExecutor(max_workers=3)


@router.get("/scrape/{ic_name}")
async def scrape_ic_datasheet(
    ic_name: str,
    save_pdf: bool = Query(True, description="Save downloaded PDF to disk")
) -> Dict[str, Any]:
    """
    Scrape IC datasheet from alldatasheet.com and extract dimensions.
    
    This endpoint performs the full automation:
    1. Searches for the IC on alldatasheet.com
    2. Downloads the datasheet PDF
    3. Extracts dimensional data using Gemini AI
    
    Args:
        ic_name: IC part number (e.g., "HT12D", "SN74HCT257N")
        save_pdf: Whether to save the PDF to the downloads directory
        
    Returns:
        JSON with chip info, PDF URL, and extracted dimensions
        
    Raises:
        HTTPException: 400 if no datasheet found, 500 for server errors
    """
    logger.info(f"API request: scrape IC {ic_name}")
    
    try:
        # Run blocking operation in threadpool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            scrape_and_extract,
            ic_name,
            save_pdf
        )
        
        # Check for errors in result
        if "error" in result:
            error_type = result.get("error", "Unknown error")
            detail = result.get("detail", "No additional details")
            
            # Determine appropriate status code
            if "not found" in error_type.lower():
                raise HTTPException(status_code=404, detail=detail)
            elif "download failed" in error_type.lower():
                raise HTTPException(status_code=400, detail=detail)
            else:
                raise HTTPException(status_code=500, detail=detail)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in scrape endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/from-file")
async def extract_from_file(
    pdf: UploadFile = File(..., description="PDF datasheet file")
) -> Dict[str, Any]:
    """
    Extract IC dimensions from an uploaded PDF file.
    
    Upload a datasheet PDF and get dimensional data extracted by Gemini AI.
    
    Args:
        pdf: PDF file upload
        
    Returns:
        JSON with filename and extracted dimensions
        
    Raises:
        HTTPException: 400 for invalid files, 500 for server errors
    """
    logger.info(f"API request: extract from file {pdf.filename}")
    
    try:
        # Validate file type
        if not pdf.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Read file bytes
        pdf_bytes = await pdf.read()
        
        if len(pdf_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        # Run Gemini extraction in threadpool
        loop = asyncio.get_event_loop()
        dimensions = await loop.run_in_executor(
            executor,
            extract_dimensions_with_gemini,
            pdf_bytes
        )
        
        # Check for extraction errors
        if "error" in dimensions:
            raise HTTPException(
                status_code=500,
                detail=f"Extraction failed: {dimensions.get('error', 'Unknown error')}"
            )
        
        return {
            "file": pdf.filename,
            "dimensions": dimensions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in from-file endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/from-url")
async def extract_from_url(
    pdf_url: str = Form(..., description="Direct URL to PDF datasheet")
) -> Dict[str, Any]:
    """
    Extract IC dimensions from a PDF URL.
    
    Provide a direct URL to a datasheet PDF and get dimensional data.
    
    Args:
        pdf_url: Direct URL to PDF file
        
    Returns:
        JSON with PDF URL and extracted dimensions
        
    Raises:
        HTTPException: 400 for download failures, 500 for server errors
    """
    logger.info(f"API request: extract from URL {pdf_url}")
    
    try:
        # Validate URL format
        if not pdf_url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=400,
                detail="Invalid URL format. Must start with http:// or https://"
            )
        
        # Download PDF in threadpool
        loop = asyncio.get_event_loop()
        temp_path = f"temp_download.pdf"
        
        download_result = await loop.run_in_executor(
            executor,
            download_pdf,
            pdf_url,
            temp_path
        )
        
        if not download_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to download PDF: {download_result.get('error', 'Unknown error')}"
            )
        
        # Read downloaded file
        with open(temp_path, "rb") as f:
            pdf_bytes = f.read()
        
        # Extract dimensions in threadpool
        dimensions = await loop.run_in_executor(
            executor,
            extract_dimensions_with_gemini,
            pdf_bytes
        )
        
        # Clean up temp file
        try:
            import os
            os.remove(temp_path)
        except:
            pass
        
        # Check for extraction errors
        if "error" in dimensions:
            raise HTTPException(
                status_code=500,
                detail=f"Extraction failed: {dimensions.get('error', 'Unknown error')}"
            )
        
        return {
            "pdf_url": pdf_url,
            "dimensions": dimensions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in from-url endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for the extraction service.
    
    Returns:
        Status message
    """
    return {
        "status": "healthy",
        "service": "IC Datasheet Extractor"
    }
