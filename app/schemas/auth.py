from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


INDIAN_MOBILE = r"^[6-9]\d{9}$"


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    mobile: str = Field(..., pattern=INDIAN_MOBILE, examples=["9876543210"])
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(..., description="Registered email or mobile number")
    password: str


class ProfileUpdateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    mobile: str = Field(..., pattern=INDIAN_MOBILE)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
