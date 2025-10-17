from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class DatabaseException(AppException):
    def __init__(self, internal_detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                         detail="Something went wrong. Please try again later.")
        self.internal_detail = internal_detail


class NotFoundException(AppException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND,
                         detail=detail)


class UserAlreadyExistsException(AppException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST,
                         detail=detail)


class InvalidCredentialsException(AppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="Invalid credentials")


class InvalidTokenException(AppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="Invalid token")