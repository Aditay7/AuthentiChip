import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.client import get_database
from app.models.ic_database import ICRecordCreate, ICRecordOut, ICRecordUpdate
from app.repositories.ic_repository import ICRepository
from app.services.web_scapper.web_scrapper import scrape_and_extract

# Configure logging
logger = logging.getLogger(__name__)

# Thread pool for blocking scraper operations
executor = ThreadPoolExecutor(max_workers=3)

router = APIRouter(prefix="/ic", tags=["ic"])


def get_ic_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> ICRepository:
    """Dependency to get IC repository instance"""
    return ICRepository(db)


def prepare_ic_record_from_scrape(dimensions: dict) -> dict:
    """
    Convert scraped dimensions data to IC record format.
    Sets missing fields to None/default values.
    """
    return {
        "manufacturer": dimensions.get("manufacturer", "Unknown"),
        "full_part_number": dimensions.get("full_part_numbers", "Unknown"),
        "allowed_markings": dimensions.get("allowed_markings", []),
        "package_type": dimensions.get("package_type", "Unknown"),
        "package_dimensions": dimensions.get("package_dimensions"),
        "image_data": {
            "original_image_path": None,
            "cropped_image_path": None,
            "content_type": "image/jpeg"
        },
        "dimensions_match": False,  # Not verified yet
        "texture_model_confidence_score": 0,  # Not analyzed yet
        "overall_confidence_score": 0  # Not analyzed yet
    }



@router.post("", response_model=ICRecordOut, status_code=status.HTTP_201_CREATED)
async def create_ic_record(
    ic_in: ICRecordCreate,
    repo: ICRepository = Depends(get_ic_repository)
) -> ICRecordOut:
    """Create a new IC record"""
    ic_data = ic_in.model_dump()
    created = await repo.create(ic_data)
    return ICRecordOut(
        id=str(created["_id"]),
        **{k: v for k, v in created.items() if k != "_id"}
    )


@router.get("", response_model=List[ICRecordOut])
async def list_ic_records(
    manufacturer: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    repo: ICRepository = Depends(get_ic_repository)
) -> List[ICRecordOut]:
    """List IC records with optional filters"""
    filters = {}
    if manufacturer:
        filters["manufacturer"] = manufacturer
    
    records = await repo.list(filters, skip=skip, limit=limit)
    return [
        ICRecordOut(
            id=str(record["_id"]),
            **{k: v for k, v in record.items() if k != "_id"}
        )
        for record in records
    ]


@router.get("/search/{full_part_number}", response_model=ICRecordOut)
async def search_by_full_part_number(
    full_part_number: str,
    repo: ICRepository = Depends(get_ic_repository),
    auto_scrape: bool = True
) -> ICRecordOut:
    """
    Search IC record by full part number (e.g., LM358N, STM32F103C8T6).
    
    If not found and auto_scrape=True, automatically scrapes datasheet from 
    alldatasheet.com and saves to database.
    
    Args:
        full_part_number: The full part number to search for
        auto_scrape: Enable automatic web scraping if not found (default: True)
    
    Returns:
        IC record with complete details
    
    Raises:
        404: IC not found (and scraping failed or disabled)
    """
    # 1. Try to find in database first
    record = await repo.search_by_full_part_number(full_part_number)
    
    if record:
        logger.info(f"Found IC in database: {full_part_number}")
        return ICRecordOut(
            id=str(record["_id"]),
            **{k: v for k, v in record.items() if k != "_id"}
        )
    
    # 2. If not found and auto_scrape enabled, trigger web scraper
    if auto_scrape:
        logger.info(f"IC not found in database, triggering auto-scrape: {full_part_number}")
        
        try:
            # Run scraper in threadpool (non-blocking)
            loop = asyncio.get_event_loop()
            scrape_result = await loop.run_in_executor(
                executor,
                scrape_and_extract,
                full_part_number,
                False  # Don't save PDF to disk
            )
            
            # 3. Check if scraping was successful
            if "error" not in scrape_result and "dimensions" in scrape_result:
                logger.info(f"Successfully scraped datasheet for: {full_part_number}")
                
                # 4. Prepare IC record from scraped data
                ic_data = prepare_ic_record_from_scrape(scrape_result["dimensions"])
                
                # 5. Save to database
                created = await repo.create(ic_data)
                logger.info(f"Saved scraped IC to database: {full_part_number} (ID: {created['_id']})")
                
                # 6. Return the newly created record
                return ICRecordOut(
                    id=str(created["_id"]),
                    **{k: v for k, v in created.items() if k != "_id"}
                )
            else:
                # Scraping failed (no datasheet found)
                error_detail = scrape_result.get("detail", "Unknown error")
                logger.warning(f"Scraping failed for {full_part_number}: {error_detail}")
                
        except Exception as e:
            # Log error but continue to 404
            logger.error(f"Auto-scrape exception for {full_part_number}: {str(e)}")
    
    # 7. If scraping failed or disabled, return 404
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"IC record with full part number '{full_part_number}' not found"
    )


@router.get("/{ic_id}", response_model=ICRecordOut)
async def get_ic_record(
    ic_id: str,
    repo: ICRepository = Depends(get_ic_repository)
) -> ICRecordOut:
    """Get a single IC record by ID"""
    record = await repo.get_by_id(ic_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IC record with id {ic_id} not found"
        )
    return ICRecordOut(
        id=str(record["_id"]),
        **{k: v for k, v in record.items() if k != "_id"}
    )


@router.patch("/{ic_id}", response_model=ICRecordOut)
async def update_ic_record(
    ic_id: str,
    ic_update: ICRecordUpdate,
    repo: ICRepository = Depends(get_ic_repository)
) -> ICRecordOut:
    """Update an IC record"""
    # Check if record exists
    existing = await repo.get_by_id(ic_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IC record with id {ic_id} not found"
        )
    
    # Perform update
    update_data = ic_update.model_dump(exclude_unset=True)
    updated = await repo.update(ic_id, update_data)
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update IC record"
        )
    
    return ICRecordOut(
        id=str(updated["_id"]),
        **{k: v for k, v in updated.items() if k != "_id"}
    )


@router.delete("/{ic_id}")
async def delete_ic_record(
    ic_id: str,
    repo: ICRepository = Depends(get_ic_repository)
) -> dict:
    """Delete an IC record"""
    success = await repo.delete(ic_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IC record with id {ic_id} not found"
        )
    return {"message": f"IC record {ic_id} deleted successfully"}
