import secrets
from typing import Dict, Optional

from passlib.context import CryptContext

from app.models.user import UserCreate, UserLogin, UserOut
from app.repositories.user_repo import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def signup(self, payload: UserCreate) -> UserOut:
        existing = await self.repo.get_by_email(payload.email)
        if existing:
            raise ValueError("User already exists")

        hashed_password = pwd_context.hash(payload.password)
        data = {"email": payload.email, "password_hash": hashed_password}
        created = await self.repo.create(data)
        return UserOut(id=str(created["_id"]), email=created["email"])

    async def login(self, payload: UserLogin) -> Dict[str, str]:
        user = await self.repo.get_by_email(payload.email)
        if not user:
            raise ValueError("Invalid credentials")

        if not pwd_context.verify(payload.password, user.get("password_hash", "")):
            raise ValueError("Invalid credentials")

        token = secrets.token_urlsafe(32)
        return {"access_token": token, "token_type": "bearer"}

