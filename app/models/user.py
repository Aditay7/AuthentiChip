from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: str = Field(default="worker", description="Role enum: admin|worker")
    contact: Optional[str] = None
    organization: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: str
    last_active: Optional[datetime] = None

