from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_async_session, get_current_user
from app.core.security import AuthService
from app.services.user_service import UserService
from app.api.v1.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, TokenRequest
from app.models.user import User
from app.core.logging_config import setup_logger


logger = setup_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_async_session)):
    existing_user = await UserService.get_user_by_email(session, user_data.email)
    if existing_user:
        logger.warning(f"Registration attempt with existing email: {user_data.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = AuthService.get_password_hash(user_data.password)
    user = await UserService.create_user(session, user_data.username, user_data.email, hashed_password)
    logger.info(f"User registered: {user.email}")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, session: AsyncSession = Depends(get_async_session)):
    user = await UserService.authenticate_user(session, user_data.email, user_data.password)
    if not user:
        logger.warning(f"Login failed for email: {user_data.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = AuthService.create_access_token({"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token({"sub": str(user.id)})
    logger.info(f"User logged in: {user.email}")
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    logger.info(f"User accessed /me: {current_user.email}")
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRequest,
    session: AsyncSession = Depends(get_async_session)
):
    user = await AuthService.get_current_user(token_data.refresh_token, session, expected_type="refresh")
    access_token = AuthService.create_access_token({"sub": str(user.id)})
    logger.info(f"Token refreshed for user: {user.email}")
    return {"access_token": access_token, "refresh_token": token_data.token, "token_type": "bearer"}