from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.repositories.user_repository import user_repository
from app.services.exceptions import ForbiddenError, UnauthorizedError


bearer_scheme = HTTPBearer(auto_error=False)


def _user_from_token(credentials: HTTPAuthorizationCredentials | None) -> dict | None:
    if credentials is None:
        return None

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token, please login again")

    user = user_repository.get_by_id(int(payload["sub"]))
    if user is None or not user["is_active"]:
        raise UnauthorizedError("User not found or blocked")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    user = _user_from_token(credentials)
    if user is None:
        raise UnauthorizedError("Please login to continue")
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict | None:
    """For guest-friendly APIs (product details shows is_wishlisted when logged in)."""
    return _user_from_token(credentials)


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise ForbiddenError("Admin access required")
    return user
