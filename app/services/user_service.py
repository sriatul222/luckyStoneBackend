from app.repositories.user_repository import user_repository
from app.schemas.common import page_data
from app.schemas.user import UserResponse
from app.services.exceptions import BadRequestError, NotFoundError


class UserService:
    def get_users(self, page: int, page_size: int) -> dict:
        users, total = user_repository.get_all(page_size, (page - 1) * page_size)
        items = [UserResponse.model_validate(user) for user in users]
        return page_data(items, page, page_size, total)

    def set_role(self, admin: dict, user_id: int, role: str) -> dict:
        if admin["id"] == user_id and role != "admin":
            raise BadRequestError("You cannot remove your own admin access")
        user = user_repository.set_role(user_id, role)
        if user is None:
            raise NotFoundError("User not found")
        return user

    def set_active(self, admin: dict, user_id: int, is_active: bool) -> dict:
        if admin["id"] == user_id and not is_active:
            raise BadRequestError("You cannot block yourself")
        user = user_repository.set_active(user_id, is_active)
        if user is None:
            raise NotFoundError("User not found")
        return user


user_service = UserService()
