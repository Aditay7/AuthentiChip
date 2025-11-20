from typing import Dict

from app.core.security import create_access_token
from app.models.user import UserCreate, UserLogin, UserOut
from app.repositories.user_repo import UserRepository


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def signup(self, payload: UserCreate) -> UserOut:
        existing = await self.repo.get_by_email(payload.email)
        if existing:
            raise ValueError("User already exists")

        
        data = {
            "email": payload.email,
            "password": payload.password,  # Plain text for simplicity
            "name": payload.name,
            "role": payload.role,
            "contact": payload.contact,
            "organization": payload.organization,
            "is_active": True,
            "last_active": None,
        }
        created = await self.repo.create(data)
        return UserOut(
            id=str(created["_id"]),
            email=created["email"],
            name=created.get("name"),
            role=created.get("role", "worker"),
            contact=created.get("contact"),
            organization=created.get("organization"),
            last_active=created.get("last_active"),
        )

    async def login(self, payload: UserLogin) -> Dict[str, str]:
        user = await self.repo.get_by_email(payload.email)
        if not user:
            raise ValueError("Invalid credentials")

        # Simple plain text comparison
        if user.get("password") != payload.password:
            raise ValueError("Invalid credentials")

        await self.repo.update_last_active(str(user["_id"]))
        token = create_access_token(str(user["_id"]))
        return {"access_token": token, "token_type": "bearer"}

