from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db, require_admin
from app.models.admin import AdminCreate, AdminOut, AdminUpdate
from app.repositories.user_repo import UserRepository
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admins", tags=["admins"])


def get_admin_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> AdminService:
    return AdminService(UserRepository(db))


@router.post("", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    payload: AdminCreate,
    current_admin: dict = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminOut:
    try:
        return await service.create_user(payload, current_admin)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get("", response_model=list[AdminOut])
async def list_admin_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    include_inactive: bool = Query(False),
    current_admin: dict = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
) -> list[AdminOut]:
    return await service.list_users(current_admin, role=role, include_inactive=include_inactive)


@router.patch("/{user_id}", response_model=AdminOut)
async def update_admin_user(
    user_id: str,
    payload: AdminUpdate,
    current_admin: dict = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminOut:
    try:
        return await service.update_user(user_id, payload, current_admin)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_user(
    user_id: str,
    current_admin: dict = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
) -> None:
    try:
        await service.deactivate_user(user_id, current_admin)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

