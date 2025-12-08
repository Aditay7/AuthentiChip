from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase


class ScanRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db["scans"]

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new scan record"""
        result = await self.collection.insert_one(data)
        return {**data, "_id": result.inserted_id}

    async def get_by_id(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan record by ID"""
        db_id = self._to_object_id(scan_id)
        if db_id is None:
            return None
        return await self.collection.find_one({"_id": db_id})

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List scan records with optional filters and pagination"""
        query = filters or {}
        cursor = (
            self.collection.find(query)
            .skip(max(skip, 0))
            .limit(min(limit, 100))
            .sort("scanned_at", -1)  # Most recent first
        )
        return [doc async for doc in cursor]

    async def update(self, scan_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update scan record by ID"""
        db_id = self._to_object_id(scan_id)
        if db_id is None:
            return None
        
        # Remove None values from updates to support partial updates
        clean_updates = {k: v for k, v in updates.items() if v is not None}
        
        if not clean_updates:
            return await self.get_by_id(scan_id)
        
        await self.collection.update_one({"_id": db_id}, {"$set": clean_updates})
        return await self.get_by_id(scan_id)

    @staticmethod
    def _to_object_id(scan_id: str) -> Optional[ObjectId]:
        """Convert string ID to ObjectId"""
        try:
            return ObjectId(scan_id)
        except (InvalidId, TypeError):
            return None
