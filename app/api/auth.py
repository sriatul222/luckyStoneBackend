from fastapi import APIRouter, Depends, status

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    TokenData,
)
from app.schemas.common import ApiResponse
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service


router = APIRouter(prefix=f"{settings.api_prefix}/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[TokenData])
def register(register_data: RegisterRequest):
    return {
        "success": True,
        "message": "Registration successful",
        "data": auth_service.register_user(register_data),
    }


@router.post("/login", response_model=ApiResponse[TokenData])
def login(login_data: LoginRequest):
    return {
        "success": True,
        "message": "Login successful",
        "data": auth_service.login_user(login_data),
    }


@router.get("/me", response_model=ApiResponse[UserResponse])
def get_profile(user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Profile fetched successfully", "data": user}


@router.put("/me", response_model=ApiResponse[UserResponse])
def update_profile(profile_data: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "message": "Profile updated successfully",
        "data": auth_service.update_profile(user, profile_data),
    }


@router.post("/change-password", response_model=ApiResponse)
def change_password(password_data: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    auth_service.change_password(user, password_data)
    return {"success": True, "message": "Password changed successfully", "data": None}
