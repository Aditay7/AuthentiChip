from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.client import get_database
from app.models.ic_database import ICRecordCreate, ICRecordOut, ICRecordUpdate
from app.repositories.ic_repository import ICRepository

router = APIRouter(prefix="/ic", tags=["ic"])


def get_ic_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> ICRepository:
    """Dependency to get IC repository instance"""
    return ICRepository(db)


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
    base_part_number: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    repo: ICRepository = Depends(get_ic_repository)
) -> List[ICRecordOut]:
    """List IC records with optional filters"""
    filters = {}
    if manufacturer:
        filters["manufacturer"] = manufacturer
    if base_part_number:
        filters["base_part_number"] = base_part_number
    
    records = await repo.list(filters, skip=skip, limit=limit)
    return [
        ICRecordOut(
            id=str(record["_id"]),
            **{k: v for k, v in record.items() if k != "_id"}
        )
        for record in records
    ]


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
