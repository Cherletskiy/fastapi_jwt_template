import pytest
from unittest.mock import patch
import random


@pytest.mark.asyncio
class TestAuthIntegration:

    @patch("app.core.dependencies.get_async_session")
    async def test_full_auth_flow_with_real_db(self, mock_get_async_session, test_db, client):
        """Полный цикл аутентификации с реальной БД"""

        # Мокаем сессию - создаем новую для каждого вызова
        mock_get_async_session.return_value = test_db

        # Уникальные данные для теста
        email = f"test_{random.randint(1, 999999)}@example.com"
        username = f"user_{random.randint(1, 999999)}"

        # 1. РЕГИСТРАЦИЯ
        reg_data = {
            "username": username,
            "email": email,
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
            "first_name": "Test",
            "last_name": "User",
            "middle_name": "Middle"
        }

        reg_response = client.post("/api/v1/auth/register", json=reg_data)
        assert reg_response.status_code == 200
        assert reg_response.json()["email"] == email
        user_id = reg_response.json()["id"]

        # Даем время на завершение транзакции
        import asyncio
        await asyncio.sleep(0.1)

        # 2. ЛОГИН
        login_response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "StrongPass123"
        })
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

        access_token = login_response.json()["access_token"]
        refresh_token = login_response.cookies.get("refresh_token")
        assert refresh_token is not None

        # 3. ПРОФИЛЬ
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v1/users/me", headers=headers)
        assert me_response.status_code == 200

        me_data = me_response.json()
        assert me_data["email"] == email
        assert me_data["username"] == username
        assert me_data["first_name"] == "Test"
        assert me_data["last_name"] == "User"

        # 4. ОБНОВЛЕНИЕ ПРОФИЛЯ
        update_response = client.patch("/api/v1/users/me",
                                       json={"first_name": "UpdatedName"},
                                       headers=headers
                                       )
        assert update_response.status_code == 200
        assert update_response.json()["first_name"] == "UpdatedName"

        # 5. ОБНОВЛЕНИЕ ТОКЕНА
        refresh_response = client.post("/api/v1/auth/refresh",
                                       cookies={"refresh_token": refresh_token}
                                       )
        assert refresh_response.status_code == 200
        assert "access_token" in refresh_response.json()

        new_access_token = refresh_response.json()["access_token"]
        new_refresh_token = refresh_response.cookies.get("refresh_token")
        assert new_refresh_token is not None

        # 6. ВЫХОД
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        logout_response = client.post("/api/v1/auth/logout", headers=new_headers)
        assert logout_response.status_code == 200

        # 7. ПРОВЕРКА ДОСТУПА ПОСЛЕ ВЫХОДА
        me_after_logout = client.get("/api/v1/users/me", headers=new_headers)
        assert me_after_logout.status_code == 401

    @patch("app.core.dependencies.get_async_session")
    async def test_user_roles_integration(self, mock_get_async_session, test_db, client):
        """Тест RBAC ролей с реальной БД"""

        mock_get_async_session.return_value = test_db

        email = f"role_test_{random.randint(1, 999999)}@example.com"
        username = f"role_user_{random.randint(1, 999999)}"

        # Регистрация пользователя (должен получить роль 'user')
        reg_response = client.post("/api/v1/auth/register", json={
            "username": username,
            "email": email,
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
            "first_name": "Role",
            "last_name": "Test",
            "middle_name": "User"
        })
        assert reg_response.status_code == 200

        # Даем время на завершение транзакции
        import asyncio
        await asyncio.sleep(0.1)

        # Логин
        login_response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "StrongPass123"
        })
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Проверка что у user роли нет доступа к админке
        moderation_response = client.get("/api/v1/admin/moderation", headers=headers)
        assert moderation_response.status_code == 403

        admin_response = client.get("/api/v1/admin/admin_panel", headers=headers)
        assert admin_response.status_code == 403

        # Но есть доступ к обычным эндпоинтам
        me_response = client.get("/api/v1/users/me", headers=headers)
        assert me_response.status_code == 200

        update_response = client.patch("/api/v1/users/me",
                                       json={"last_name": "Updated"},
                                       headers=headers
                                       )
        assert update_response.status_code == 200

    @patch("app.core.dependencies.get_async_session")
    async def test_deactivate_user_flow(self, mock_get_async_session, test_db, client):
        """Тест деактивации пользователя"""

        mock_get_async_session.return_value = test_db

        email = f"deactivate_{random.randint(1, 999999)}@example.com"
        username = f"deactivate_{random.randint(1, 999999)}"

        # Регистрация и логин
        reg_response = client.post("/api/v1/auth/register", json={
            "username": username,
            "email": email,
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
            "first_name": "Deactivate",
            "last_name": "Test",
            "middle_name": "User"
        })
        assert reg_response.status_code == 200

        import asyncio
        await asyncio.sleep(0.1)

        login_response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "StrongPass123"
        })
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Деактивация аккаунта
        deactivate_response = client.delete("/api/v1/users/deactivate", headers=headers)
        assert deactivate_response.status_code == 200
        assert "deactivated" in deactivate_response.json()["message"]

        # Попытка доступа после деактивации
        me_after_deactivate = client.get("/api/v1/users/me", headers=headers)
        assert me_after_deactivate.status_code == 401  # Доступ запрещен

    @patch("app.core.dependencies.get_async_session")
    async def test_registration_validation(self, mock_get_async_session, test_db, client):
        """Тест валидации при регистрации"""

        mock_get_async_session.return_value = test_db

        # Невалидный email
        invalid_email_response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
            "first_name": "Test",
            "last_name": "User",
            "middle_name": "Middle"
        })
        assert invalid_email_response.status_code == 422

        # Пароли не совпадают
        password_mismatch_response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123",
            "confirm_password": "DifferentPass123",
            "first_name": "Test",
            "last_name": "User",
            "middle_name": "Middle"
        })
        assert password_mismatch_response.status_code == 422

        # Слабый пароль
        weak_password_response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",
            "confirm_password": "weak",
            "first_name": "Test",
            "last_name": "User",
            "middle_name": "Middle"
        })
        assert weak_password_response.status_code == 422