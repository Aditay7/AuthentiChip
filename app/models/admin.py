from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class AdminCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    role: Literal["admin", "worker"] = Field(default="worker")
    contact: Optional[str] = None
    organization: Optional[str] = None


class AdminUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[Literal["admin", "worker"]] = None
    contact: Optional[str] = None
    organization: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class AdminOut(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    role: Literal["admin", "worker"]
    contact: Optional[str] = None
    organization: Optional[str] = None
    is_active: bool = True

