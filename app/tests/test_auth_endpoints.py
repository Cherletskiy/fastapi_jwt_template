from unittest.mock import patch
from unittest.mock import MagicMock
from datetime import datetime

from app.models.user import User

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
            mock_user,
            client
    ):
        """Тест успешной регистрации"""
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
    def test_register_existing_email(mock_get_user, mock_user, client):
        """Тест регистрации с существующим email"""
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

    def test_register_invalid_email(self, client):
        """Тест регистрации с некорректным email, проверка валидации EmailStr"""
        user_data = {
            "username": "testuser",
            "email": "test",
            "password": "Test12345",
            "confirm_password": "Test12345",
            "first_name": "Ivan",
            "last_name": "Petrov",
            "middle_name": "Sergeevich"
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
        assert "not a valid email" in response.json()["detail"][0]["msg"]

    def test_register_invalid_password(self, client):
        """Тест регистрации с некорректным паролем. Проверка валидации @field_validator("password")"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",
            "confirm_password": "weak",
            "first_name": "Ivan",
            "last_name": "Petrov",
            "middle_name": "Sergeevich"
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
        assert "Password must be" in response.json()["detail"][0]["msg"]

    def test_register_password_mismatch(self, client):
        """Тест регистрации с некорректным паролем. Проверка валидации @field_validator("confirm_password")"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test12345",
            "confirm_password": "Test123456",
            "first_name": "Ivan",
            "last_name": "Petrov",
            "middle_name": "Sergeevich"
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
        assert "do not match" in response.json()["detail"][0]["msg"]

    def test_register_missing_fields(self, client):
        """Тест регистрации с отсутствующими обязательными полями"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test12345",
            "confirm_password": "Test12345",
            "last_name": "Petrov",
            "middle_name": "Sergeevich"
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
        assert "Field required" in response.json()["detail"][0]["msg"]


    @patch("app.api.v1.auth.UserService.authenticate_user")
    def test_login_success(self, mock_authenticate, mock_user, client):
        """Тест логина с корректными данными"""
        mock_authenticate.return_value = mock_user

        login_data = {"email": "test@example.com", "password": "correct_password"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
        assert "refresh_token" in response.cookies

    def test_login_invalid_data(self, client):
        """Тест логина с невалидными данными"""
        login_data = {"email": "invalid-email", "password": "pass"}

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 422

    def test_login_wrong_data(self, client):
        """Тест логина с некорректными данными"""
        login_data = {"email": "test@example.com", "password": "wrong_password"}

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @patch("app.core.dependencies.AuthService.get_current_user")
    def test_get_me_success(self, mock_get_current_user, mock_user, valid_access_token, client):
        """Тест /me с корректными данными"""
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

    def test_get_me_unauthorized(self, client):
        """Тест защищенного эндпоинта без токена"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Тест защищенного эндпоинта с некорректным токена"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401

    @patch("app.core.dependencies.AuthService.get_current_user")
    def test_logout_success(self, mock_get_current_user, mock_user, valid_access_token, client):
        """Тест выхода, сброс куки"""
        mock_get_current_user.return_value = mock_user

        headers = {"Authorization": f"Bearer {valid_access_token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

        set_cookie_header = response.headers.get("set-cookie", "")

        assert "refresh_token" in set_cookie_header
        assert "Max-Age=0" in set_cookie_header

    @patch("app.core.security.AuthService.get_current_user")
    def test_refresh_token_success(mock_get_current_user, mock_user, valid_refresh_token, client):
        """Тест рефреш токена с корректным токеном"""
        mock_get_current_user.return_value = mock_user

        response = client.post("/api/v1/auth/refresh", cookies={"refresh_token": valid_refresh_token})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_token_missing(self, client):
        """Тест рефреш токена без токена"""
        client.cookies.clear()
        response = client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert response.json()["detail"] == "No refresh token provided"

    def test_refresh_token_invalid(self, client):
        """Тест рефреш токена с некорректным токеном"""
        cookies = {"refresh_token": "invalid_refresh_token"}
        response = client.post("/api/v1/auth/refresh", cookies=cookies)
        assert response.status_code == 401

    @patch("app.services.authorization_service.AuthorizationService.get_user_role_names")
    @patch("app.core.dependencies.AuthService.get_current_user")
    def test_moderation_dashboard_access_with_moderator_role(
            self, mock_get_current_user, mock_get_user_roles, valid_access_token, client
    ):
        """Тест доступа к moderation dashboard с ролью moderator"""
        moderator_user = MagicMock(spec=User)
        moderator_user.id = 2
        moderator_user.username = "moderator_user"
        moderator_user.email = "moderator@example.com"

        mock_get_current_user.return_value = moderator_user
        mock_get_user_roles.return_value = ["moderator"]

        headers = {"Authorization": f"Bearer {valid_access_token}"}
        response = client.get("/api/v1/admin/moderation", headers=headers)

        assert response.status_code == 200

    @patch("app.services.authorization_service.AuthorizationService.get_user_role_names")
    @patch("app.core.dependencies.AuthService.get_current_user")
    def test_moderation_dashboard_access_with_admin_role(
            self, mock_get_current_user, mock_get_user_roles, valid_access_token, client):
        """Тест доступа к moderation dashboard с ролью admin"""
        admin_user = MagicMock(spec=User)
        admin_user.id = 1
        admin_user.username = "admin_user"
        admin_user.email = "admin@example.com"

        mock_get_current_user.return_value = admin_user
        mock_get_user_roles.return_value = ["admin"]

        headers = {"Authorization": f"Bearer {valid_access_token}"}
        response = client.get("/api/v1/admin/moderation", headers=headers)

        assert response.status_code == 200

    @patch("app.services.authorization_service.AuthorizationService.get_user_role_names")
    @patch("app.core.dependencies.AuthService.get_current_user")
    def test_moderation_dashboard_denied_with_user_role(
            self, mock_get_current_user, mock_get_user_roles, valid_access_token, client
    ):
        """Тест запрета доступа к moderation dashboard с ролью user"""
        regular_user = MagicMock(spec=User)
        regular_user.id = 3
        regular_user.username = "regular_user"
        regular_user.email = "user@example.com"

        mock_get_current_user.return_value = regular_user
        mock_get_user_roles.return_value = ["user"]

        headers = {"Authorization": f"Bearer {valid_access_token}"}
        response = client.get("/api/v1/admin/moderation", headers=headers)

        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    @patch("app.services.authorization_service.AuthorizationService.get_user_role_names")
    @patch("app.core.dependencies.AuthService.get_current_user")
    def test_admin_panel_access_with_admin_role(
            self, mock_get_current_user, mock_get_user_roles, valid_access_token, client
    ):
        """Тест доступа к admin panel с ролью admin"""
        admin_user = MagicMock(spec=User)
        admin_user.id = 1
        admin_user.username = "admin_user"
        admin_user.email = "admin@example.com"

        mock_get_current_user.return_value = admin_user
        mock_get_user_roles.return_value = ["admin"]

        headers = {"Authorization": f"Bearer {valid_access_token}"}
        response = client.get("/api/v1/admin/admin_panel", headers=headers)

        assert response.status_code == 200


    @patch("app.services.authorization_service.AuthorizationService.get_user_role_names")
    @patch("app.core.dependencies.AuthService.get_current_user")
    def test_admin_panel_denied_with_moderator_role(
            self, mock_get_current_user, mock_get_user_roles, valid_access_token, client
    ):
        """Тест запрета доступа к admin panel с ролью moderator"""
        moderator_user = MagicMock(spec=User)
        moderator_user.id = 2
        moderator_user.username = "moderator_user"
        moderator_user.email = "moderator@example.com"

        mock_get_current_user.return_value = moderator_user
        mock_get_user_roles.return_value = ["moderator"]

        headers = {"Authorization": f"Bearer {valid_access_token}"}
        response = client.get("/api/v1/admin/admin_panel", headers=headers)

        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    @patch("app.services.authorization_service.AuthorizationService.get_user_role_names")
    @patch("app.core.dependencies.AuthService.get_current_user")
    def test_admin_panel_denied_with_user_role(
            self, mock_get_current_user, mock_get_user_roles, valid_access_token, client
    ):
        """Тест запрета доступа к moderation dashboard с ролью user"""
        regular_user = MagicMock(spec=User)
        regular_user.id = 3
        regular_user.username = "regular_user"
        regular_user.email = "user@example.com"

        mock_get_current_user.return_value = regular_user
        mock_get_user_roles.return_value = ["user"]

        headers = {"Authorization": f"Bearer {valid_access_token}"}
        response = client.get("/api/v1/admin/admin_panel", headers=headers)

        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
