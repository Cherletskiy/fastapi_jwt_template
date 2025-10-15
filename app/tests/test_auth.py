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
        created_at=datetime.utcnow()
    )


@pytest.fixture
def valid_access_token(mock_user):
    return AuthService.create_access_token({"sub": str(mock_user.id)})


@pytest.fixture
def valid_refresh_token(mock_user):
    return AuthService.create_refresh_token({"sub": str(mock_user.id)})


class TestAuthEndpoints:

    @patch('app.api.v1.auth.UserService.get_user_by_email')
    @patch('app.api.v1.auth.UserService.create_user')
    @patch('app.api.v1.auth.AuthService.get_password_hash')
    def test_register_success(self, mock_hash, mock_create_user, mock_get_user, mock_user):
        mock_get_user.return_value = None
        mock_hash.return_value = "hashed_password_123"
        mock_create_user.return_value = mock_user

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 200
        assert response.json()["email"] == user_data["email"]
        assert response.json()["username"] == user_data["username"]
        assert "id" in response.json()
        assert "created_at" in response.json()

    @patch('app.api.v1.auth.UserService.get_user_by_email')
    def test_register_existing_email(self, mock_get_user, mock_user):
        mock_get_user.return_value = mock_user

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_register_invalid_password(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak"
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

    @patch('app.api.v1.auth.UserService.authenticate_user')
    def test_login_success(self, mock_authenticate, mock_user):
        mock_authenticate.return_value = mock_user

        login_data = {
            "email": "test@example.com",
            "password": "correct_password"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
        assert "refresh_token" in response.cookies

    @patch('app.api.v1.auth.UserService.authenticate_user')
    def test_login_invalid_credentials(self, mock_authenticate):
        mock_authenticate.return_value = None

        login_data = {
            "email": "test@example.com",
            "password": "wrong_password"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_invalid_data(self):
        login_data = {
            "email": "invalid-email",
            "password": "pass"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 422

    @patch('app.core.dependencies.AuthService.get_current_user')
    def test_get_me_success(self, mock_get_current_user, mock_user, valid_access_token):
        mock_get_current_user.return_value = mock_user

        headers = {"Authorization": f"Bearer {valid_access_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        assert response.json()["email"] == mock_user.email
        assert response.json()["username"] == mock_user.username

    def test_get_me_unauthorized(self):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    @patch('app.core.dependencies.AuthService.get_current_user')
    def test_logout_success(self, mock_get_current_user, mock_user, valid_access_token):
        mock_get_current_user.return_value = mock_user

        headers = {"Authorization": f"Bearer {valid_access_token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out"

        set_cookie_header = response.headers.get("set-cookie")
        assert set_cookie_header is not None
        assert "refresh_token" in set_cookie_header
        assert "Max-Age=0" in set_cookie_header

    @patch('app.core.dependencies.AuthService.get_current_user')
    def test_refresh_token_success(self, mock_get_current_user, mock_user, valid_refresh_token):
        mock_get_current_user.return_value = mock_user

        cookies = {"refresh_token": valid_refresh_token}
        response = client.post("/api/v1/auth/refresh", cookies=cookies)

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
        assert "refresh_token" in response.cookies

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

    @patch('app.api.v1.auth.UserService.get_user_by_email')
    @patch('app.api.v1.auth.UserService.create_user')
    @patch('app.api.v1.auth.UserService.authenticate_user')
    @patch('app.core.dependencies.AuthService.get_current_user')
    def test_full_auth_flow(self, mock_get_current_user, mock_authenticate, mock_create_user, mock_get_user, mock_user):
        mock_get_user.return_value = None
        mock_create_user.return_value = mock_user
        mock_authenticate.return_value = mock_user
        mock_get_current_user.return_value = mock_user

        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123"
        }

        register_response = client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == 200

        login_data = {
            "email": "test@example.com",
            "password": "StrongPass123"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200

        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200

        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == 200


@pytest.mark.asyncio
class TestAsyncAuth:

    @patch('app.services.user_service.UserRepository.get_user_by_email')
    async def test_authenticate_user_success(self, mock_get_user, mock_user):
        from app.services.user_service import UserService
        from app.core.security import AuthService

        mock_get_user.return_value = mock_user

        with patch.object(AuthService, 'verify_password', return_value=True):
            session = AsyncMock()
            result = await UserService.authenticate_user(
                session, "test@example.com", "correct_password"
            )
            assert result == mock_user

    @patch('app.services.user_service.UserRepository.get_user_by_email')
    async def test_authenticate_user_wrong_password(self, mock_get_user, mock_user):
        from app.services.user_service import UserService
        from app.core.security import AuthService

        mock_get_user.return_value = mock_user

        with patch.object(AuthService, 'verify_password', return_value=False):
            session = AsyncMock()
            result = await UserService.authenticate_user(
                session, "test@example.com", "wrong_password"
            )
            assert result is None