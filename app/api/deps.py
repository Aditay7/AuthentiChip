from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import decode_token
from app.db.client import get_database
from app.repositories.user_repo import UserRepository

security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIOMotorDatabase:
    return get_database()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    repo = UserRepository(db)
    user = await repo.get_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name"),
        "role": user.get("role", "worker"),
        "contact": user.get("contact"),
        "organization": user.get("organization"),
        "last_active": user.get("last_active"),
        "is_active": user.get("is_active", True),
    }


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user

