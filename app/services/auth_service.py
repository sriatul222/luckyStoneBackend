from psycopg.errors import UniqueViolation

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import user_repository
from app.schemas.auth import ChangePasswordRequest, LoginRequest, ProfileUpdateRequest, RegisterRequest
from app.schemas.user import UserResponse
from app.services.exceptions import (
    BadRequestError,
    ConflictError,
    EmailAlreadyRegisteredError,
    MobileAlreadyRegisteredError,
    UnauthorizedError,
)


def token_response(user: dict) -> dict:
    return {
        "access_token": create_access_token(user["id"], user["role"]),
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


class AuthService:
    def register_user(self, register_data: RegisterRequest) -> dict:
        self._check_unique(str(register_data.email), register_data.mobile)
        try:
            user = user_repository.create(
                name=register_data.name.strip(),
                email=str(register_data.email),
                mobile=register_data.mobile,
                password_hash=hash_password(register_data.password),
            )
        except UniqueViolation:
            raise ConflictError("Email or mobile number already registered")
        return token_response(user)

    def login_user(self, login_data: LoginRequest) -> dict:
        username = login_data.username.strip()
        user = (
            user_repository.get_by_email(username)
            if "@" in username
            else user_repository.get_by_mobile(username)
        )
        if user is None or not verify_password(login_data.password, user["password_hash"]):
            raise UnauthorizedError("Invalid email/mobile or password")
        if not user["is_active"]:
            raise UnauthorizedError("Your account is blocked, please contact support")
        return token_response(user)

    def update_profile(self, user: dict, profile_data: ProfileUpdateRequest) -> dict:
        self._check_unique(str(profile_data.email), profile_data.mobile, ignore_user_id=user["id"])
        try:
            return user_repository.update_profile(
                user["id"], profile_data.name.strip(), str(profile_data.email), profile_data.mobile
            )
        except UniqueViolation:
            raise ConflictError("Email or mobile number already registered")

    def change_password(self, user: dict, password_data: ChangePasswordRequest):
        if not verify_password(password_data.old_password, user["password_hash"]):
            raise BadRequestError("Old password is incorrect")
        user_repository.update_password(user["id"], hash_password(password_data.new_password))

    def _check_unique(self, email: str, mobile: str, ignore_user_id: int | None = None):
        same_email = user_repository.get_by_email(email)
        if same_email and same_email["id"] != ignore_user_id:
            raise EmailAlreadyRegisteredError()
        same_mobile = user_repository.get_by_mobile(mobile)
        if same_mobile and same_mobile["id"] != ignore_user_id:
            raise MobileAlreadyRegisteredError()


auth_service = AuthService()
