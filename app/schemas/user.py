from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    mobile: str
    role: str
    is_active: bool
    created_at: datetime


class UserRoleUpdate(BaseModel):
    role: Literal["customer", "admin"]


class UserStatusUpdate(BaseModel):
    is_active: bool
