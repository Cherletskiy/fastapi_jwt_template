import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import jwt
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.core.config import settings
from app.core.security import AuthService

client = TestClient(app)


@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_123",
        first_name="Ivan",
        last_name="Petrov",
        middle_name="Sergeevich",
        is_active=True,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def valid_access_token(mock_user):
    return AuthService.create_access_token({"sub": str(mock_user.id)})


@pytest.fixture
def valid_refresh_token(mock_user):
    return AuthService.create_refresh_token({"sub": str(mock_user.id)})


class TestAuthEndpoints:

    @patch("app.services.user_service.AuthorizationService.assign_role_to_user")
    @patch("app.services.user_service.AuthService.get_password_hash")
    @patch("app.services.user_service.UserRepository.create_user")
    @patch("app.services.user_service.UserRepository.get_user_by_email")
    def test_register_success(
            self,
            mock_get_user_by_email,
            mock_create_user,
            mock_hash,
            mock_assign_role,
            mock_user
    ):
        mock_get_user_by_email.return_value = None
        mock_hash.return_value = "hashed_password_123"
        mock_create_user.return_value = mock_user
        mock_assign_role.return_value = True

        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
            "first_name": "Ivan",
            "last_name": "Petrov",
            "middle_name": "Sergeevich"
        })

        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

    @patch("app.services.user_service.UserRepository.get_user_by_email")
    def test_register_existing_email(mock_get_user, mock_user):
        mock_get_user.return_value = mock_user

        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
            "first_name": "Ivan",
            "last_name": "Petrov",
            "middle_name": "Sergeevich"
        })

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_password(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

    @patch("app.api.v1.auth.UserService.authenticate_user")
    def test_login_success(self, mock_authenticate, mock_user):
        mock_authenticate.return_value = mock_user

        login_data = {"email": "test@example.com", "password": "correct_password"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
        assert "refresh_token" in response.cookies

    def test_login_invalid_data(self):
        login_data = {"email": "invalid-email", "password": "pass"}

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 422

    @patch("app.core.dependencies.AuthService.get_current_user")
    def test_get_me_success(self, mock_get_current_user, mock_user, valid_access_token):
        real_user_data = User(
            id=1,
            username="testuser",
            email="test@example.com",
            first_name="Ivan",
            last_name="Petrov",
            middle_name="Sergeevich",
            hashed_password="hashed",
            created_at=datetime.utcnow(),
            is_active=True
        )
        mock_get_current_user.return_value = real_user_data

        headers = {"Authorization": f"Bearer {valid_access_token}"}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
        assert response.json()["username"] == "testuser"

    def test_get_me_unauthorized(self):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401

    @patch("app.core.dependencies.AuthService.get_current_user")
    def test_logout_success(self, mock_get_current_user, mock_user, valid_access_token):
        mock_get_current_user.return_value = mock_user

        headers = {"Authorization": f"Bearer {valid_access_token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out"

        set_cookie_header = response.headers.get("set-cookie", "")
        # Проверяем что cookie устанавливается для удаления
        assert "refresh_token" in set_cookie_header
        assert "Max-Age=0" in set_cookie_header

    @patch("app.core.security.AuthService.get_current_user")
    def test_refresh_token_success(mock_get_current_user, mock_user, valid_refresh_token):
        mock_get_current_user.return_value = mock_user

        response = client.post("/api/v1/auth/refresh", cookies={"refresh_token": valid_refresh_token})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_token_missing(self):
        client.cookies.clear()
        response = client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert response.json()["detail"] == "No refresh token provided"

    def test_refresh_token_invalid(self):
        cookies = {"refresh_token": "invalid_refresh_token"}
        response = client.post("/api/v1/auth/refresh", cookies=cookies)
        assert response.status_code == 401


class TestSecurityUtils:

    def test_password_hashing(self):
        password = "TestPassword123"
        hashed = AuthService.get_password_hash(password)

        assert hashed != password
        assert isinstance(hashed, str)

    def test_password_verification(self):
        password = "TestPassword123"
        wrong_password = "WrongPassword123"

        hashed = AuthService.get_password_hash(password)

        assert AuthService.verify_password(password, hashed) is True
        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_token_creation(self, mock_user):
        user_data = {"sub": str(mock_user.id)}

        access_token = AuthService.create_access_token(user_data)
        refresh_token = AuthService.create_refresh_token(user_data)

        assert access_token is not None
        assert refresh_token is not None
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert access_token != refresh_token

    def test_token_decoding_valid(self, valid_access_token, mock_user):
        payload = AuthService.decode_token(valid_access_token, "access")

        assert payload["sub"] == str(mock_user.id)
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_token_decoding_wrong_type(self, valid_refresh_token):
        with pytest.raises(Exception):
            AuthService.decode_token(valid_refresh_token, "access")

    def test_token_decoding_invalid(self):
        invalid_token = "invalid.token.here"
        with pytest.raises(Exception):
            AuthService.decode_token(invalid_token, "access")


class TestAuthIntegration:

    @patch("app.core.dependencies.AuthService.get_current_user")
    @patch("app.services.user_service.AuthorizationService.assign_role_to_user")
    @patch("app.services.user_service.AuthService.verify_password")
    @patch("app.services.user_service.UserRepository.create_user")
    @patch("app.services.user_service.UserRepository.get_user_by_email")
    def test_full_auth_flow(
            self,
            mock_get_user_by_email,
            mock_create_user,
            mock_verify_password,
            mock_assign_role,
            mock_get_current_user,
            mock_user
    ):

        mock_get_user_by_email.return_value = None
        mock_create_user.return_value = mock_user
        mock_assign_role.return_value = True

        reg_response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
            "first_name": "Ivan",
            "last_name": "Petrov",
            "middle_name": "Sergeevich"
        })
        assert reg_response.status_code == 200

        mock_get_user_by_email.return_value = mock_user
        mock_verify_password.return_value = True
        mock_get_current_user.return_value = mock_user

        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "StrongPass123"
        })
        assert login_response.status_code == 200

        access_token = login_response.json()["access_token"]

        me_response = client.get("/api/v1/users/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        assert me_response.status_code == 200

        logout_response = client.post("/api/v1/auth/logout", headers={
            "Authorization": f"Bearer {access_token}"
        })
        assert logout_response.status_code == 200


@pytest.mark.asyncio
class TestAsyncAuth:

    @patch("app.services.user_service.UserRepository.get_user_by_email")
    async def test_authenticate_user_success(self, mock_get_user, mock_user):
        from app.services.user_service import UserService
        from app.core.security import AuthService

        mock_get_user.return_value = mock_user

        with patch.object(AuthService, "verify_password", return_value=True):
            session = AsyncMock()
            result = await UserService.authenticate_user(
                session, "test@example.com", "correct_password"
            )
            assert result == mock_user

    @patch("app.services.user_service.UserRepository.get_user_by_email")
    async def test_authenticate_user_wrong_password(self, mock_get_user, mock_user):
        from app.services.user_service import UserService
        from app.core.security import AuthService

        mock_get_user.return_value = mock_user

        with patch.object(AuthService, "verify_password", return_value=False):
            session = AsyncMock()
            with pytest.raises(Exception):
                result = await UserService.authenticate_user(
                    session, "test@example.com", "wrong_password"
                )
