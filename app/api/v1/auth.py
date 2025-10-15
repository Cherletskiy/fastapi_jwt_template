from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_async_session, get_current_user, get_refresh_token
from app.core.security import AuthService
from app.services.user_service import UserService
from app.api.v1.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from app.models.user import User
from app.core.logging_config import setup_logger
from app.core.config import settings


logger = setup_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


async def set_refresh_token_cookie(
        response: Response,
        refresh_token: str
):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # True for HTTPS
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    )


@router.post("/register", response_model=UserResponse)
async def register(
        user_data: UserCreate,
        session: AsyncSession = Depends(get_async_session)
):
    existing_user = await UserService.get_user_by_email(session, user_data.email)
    if existing_user:
        logger.warning(f"Registration attempt with existing email: {user_data.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = AuthService.get_password_hash(user_data.password)
    user = await UserService.create_user(session, user_data.username, user_data.email, hashed_password)
    logger.info(f"User registered: {user.email}")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
        response: Response,
        user_data: UserLogin,
        session: AsyncSession = Depends(get_async_session)
):
    user = await UserService.authenticate_user(session, user_data.email, user_data.password)
    if not user:
        logger.warning(f"Login failed for email: {user_data.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = AuthService.create_access_token({"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token({"sub": str(user.id)})

    await set_refresh_token_cookie(response, refresh_token)

    logger.info(f"User logged in: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
        response: Response,
        refresh_token: str = Depends(get_refresh_token),
        session: AsyncSession = Depends(get_async_session)
):
    user = await AuthService.get_current_user(refresh_token, session, expected_type="refresh")
    access_token = AuthService.create_access_token({"sub": str(user.id)})
    new_refresh_token = AuthService.create_refresh_token({"sub": str(user.id)})

    await set_refresh_token_cookie(response, new_refresh_token)

    logger.info(f"Token refreshed for user: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(
        current_user: User = Depends(get_current_user)
):
    logger.info(f"User accessed /me: {current_user.email}")
    return current_user


@router.post("/logout")
async def logout(
        response: Response,
        current_user: User = Depends(get_current_user)
):
    response.delete_cookie("refresh_token")

    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out"}
