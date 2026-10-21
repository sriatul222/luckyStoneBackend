from fastapi import status


class AppError(Exception):
    """Raised by services; turned into {"success": false, "message": ...}."""

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT


class EmailAlreadyRegisteredError(ConflictError):
    def __init__(self):
        super().__init__("Email already registered")


class MobileAlreadyRegisteredError(ConflictError):
    def __init__(self):
        super().__init__("Mobile number already registered")
