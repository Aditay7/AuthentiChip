from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db["users"]

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"email": email})

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        db_id = self._to_object_id(user_id)
        if db_id is None:
            return None
        return await self.collection.find_one({"_id": db_id})

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.collection.insert_one(data)
        return {**data, "_id": result.inserted_id}

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        cursor = (
            self.collection.find(filters or {})
            .skip(max(skip, 0))
            .limit(min(limit, 100))
            .sort("last_active", -1)
        )
        return [doc async for doc in cursor]

    async def update(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        db_id = self._to_object_id(user_id)
        if db_id is None:
            return None
        await self.collection.update_one({"_id": db_id}, {"$set": updates})
        return await self.get_by_id(user_id)

    async def soft_delete(self, user_id: str) -> bool:
        db_id = self._to_object_id(user_id)
        if db_id is None:
            return False
        result = await self.collection.update_one({"_id": db_id}, {"$set": {"is_active": False}})
        return result.modified_count > 0

    async def update_last_active(self, user_id: str) -> None:
        db_id = self._to_object_id(user_id)
        if db_id is None:
            return
        await self.collection.update_one(
            {"_id": db_id},
            {"$set": {"last_active": datetime.now(timezone.utc)}},
        )

    @staticmethod
    def _to_object_id(user_id: str) -> Optional[ObjectId]:
        try:
            return ObjectId(user_id)
        except (InvalidId, TypeError):
            return None

