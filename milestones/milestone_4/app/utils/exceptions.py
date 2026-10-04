"""bussiness errors from services.main.py sends them as json."""


class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class UnauthorizedException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class ForbiddenException(AppException):
    """logged in,but this cart or order belongs to someone else."""

    def __init__(self, message: str):
        super().__init__(message, status_code=403)
