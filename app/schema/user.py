from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: str
    email: EmailStr
    password: str
    phone: str
    name: Optional[str]
    role: str
    active: bool
    last_seen: Optional[str]
