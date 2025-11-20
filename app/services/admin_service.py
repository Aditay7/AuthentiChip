from typing import Dict, List, Optional

from app.models.admin import AdminCreate, AdminOut, AdminUpdate
from app.repositories.user_repo import UserRepository


class AdminService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def create_user(self, payload: AdminCreate, current_admin: Dict) -> AdminOut:
        self._ensure_same_org(current_admin, payload.organization)

        existing = await self.repo.get_by_email(payload.email)
        if existing:
            raise ValueError("User already exists")

        data = {
            "email": payload.email,
            "password": payload.password,  # Plain text for simplicity
            "name": payload.name,
            "role": payload.role,
            "contact": payload.contact,
            "organization": payload.organization or current_admin.get("organization"),
            "is_active": True,
            "last_active": None,
        }
        created = await self.repo.create(data)
        return self._to_admin_out(created)

    async def list_users(
        self,
        current_admin: Dict,
        *,
        role: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[AdminOut]:
        filters: Dict[str, object] = {
            "organization": current_admin.get("organization"),
        }
        if role in {"admin", "worker"}:
            filters["role"] = role
        if not include_inactive:
            filters["is_active"] = True

        users = await self.repo.list(filters=filters)
        return [self._to_admin_out(u) for u in users]

    async def update_user(self, user_id: str, payload: AdminUpdate, current_admin: Dict) -> AdminOut:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        self._ensure_same_org(current_admin, user.get("organization"))

        updates: Dict[str, object] = {}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.role is not None:
            updates["role"] = payload.role
        if payload.contact is not None:
            updates["contact"] = payload.contact
        if payload.organization is not None:
            self._ensure_same_org(current_admin, payload.organization)
            updates["organization"] = payload.organization
        if payload.password:
            updates["password"] = payload.password  # Plain text for simplicity
        if payload.is_active is not None:
            updates["is_active"] = payload.is_active

        updated = await self.repo.update(user_id, updates)
        if not updated:
            raise ValueError("Update failed")
        return self._to_admin_out(updated)

    async def deactivate_user(self, user_id: str, current_admin: Dict) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        self._ensure_same_org(current_admin, user.get("organization"))
        await self.repo.soft_delete(user_id)

    def _ensure_same_org(self, admin: Dict, organization: Optional[str]) -> None:
        admin_org = admin.get("organization")
        if admin_org and organization and admin_org != organization:
            raise PermissionError("Admins can only manage users within their organization")

    @staticmethod
    def _to_admin_out(data: Dict[str, object]) -> AdminOut:
        return AdminOut(
            id=str(data["_id"]),
            email=data["email"],
            name=data.get("name"),
            role=data.get("role", "worker"),  # type: ignore[arg-type]
            contact=data.get("contact"),
            organization=data.get("organization"),
            is_active=data.get("is_active", True),  # type: ignore[arg-type]
        )

