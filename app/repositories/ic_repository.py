from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase


class ICRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db["ic_records"]

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new IC record"""
        result = await self.collection.insert_one(data)
        return {**data, "_id": result.inserted_id}

    async def get_by_id(self, ic_id: str) -> Optional[Dict[str, Any]]:
        """Get IC record by ID"""
        db_id = self._to_object_id(ic_id)
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
        """List IC records with optional filters and pagination"""
        query = filters or {}
        cursor = (
            self.collection.find(query)
            .skip(max(skip, 0))
            .limit(min(limit, 100))
            .sort("manufacturer", 1)
        )
        return [doc async for doc in cursor]

    async def update(self, ic_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update IC record by ID"""
        db_id = self._to_object_id(ic_id)
        if db_id is None:
            return None
        
        # Remove None values from updates to support partial updates
        clean_updates = {k: v for k, v in updates.items() if v is not None}
        
        if not clean_updates:
            return await self.get_by_id(ic_id)
        
        await self.collection.update_one({"_id": db_id}, {"$set": clean_updates})
        return await self.get_by_id(ic_id)

    async def delete(self, ic_id: str) -> bool:
        """Delete IC record by ID"""
        db_id = self._to_object_id(ic_id)
        if db_id is None:
            return False
        result = await self.collection.delete_one({"_id": db_id})
        return result.deleted_count > 0

    @staticmethod
    def _to_object_id(ic_id: str) -> Optional[ObjectId]:
        """Convert string ID to ObjectId"""
        try:
            return ObjectId(ic_id)
        except (InvalidId, TypeError):
            return None
