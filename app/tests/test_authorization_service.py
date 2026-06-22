import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.authorization_service import AuthorizationService


@pytest.mark.asyncio
class TestAuthorizationService:

    @patch("app.services.authorization_service.AuthorizationRepository.get_user_permission_names")
    async def test_has_permission_true(self, mock_get_permissions):
        """Тест когда у пользователя есть разрешение"""
        mock_get_permissions.return_value = ["profile:read", "profile:write", "users:read"]

        session = AsyncMock()
        result = await AuthorizationService.has_permission(
            session, user_id=1, permission_name="profile:write"
        )

        assert result is True
        mock_get_permissions.assert_called_once_with(session, 1)

    @patch("app.services.authorization_service.AuthorizationRepository.get_user_permission_names")
    async def test_has_permission_false(self, mock_get_permissions):
        """Тест когда у пользователя нет разрешения"""
        mock_get_permissions.return_value = ["profile:read", "users:read"]

        session = AsyncMock()
        result = await AuthorizationService.has_permission(
            session, user_id=1, permission_name="admin:access"
        )

        assert result is False

    @patch("app.services.authorization_service.AuthorizationRepository.get_user_permission_names")
    async def test_has_permission_empty_list(self, mock_get_permissions):
        """Тест когда у пользователя нет никаких разрешений"""
        mock_get_permissions.return_value = []

        session = AsyncMock()
        result = await AuthorizationService.has_permission(
            session, user_id=1, permission_name="profile:read"
        )

        assert result is False

    @patch("app.services.authorization_service.AuthorizationRepository.get_user_permission_names")
    async def test_has_permission_list_success(self, mock_get_permissions):
        """Тест получения списка всех разрешений пользователя"""
        expected_permissions = ["profile:read", "profile:write", "users:read"]
        mock_get_permissions.return_value = expected_permissions

        session = AsyncMock()
        result = await AuthorizationService.has_permission_list(session, user_id=1)

        assert result == expected_permissions
        mock_get_permissions.assert_called_once_with(session, 1)

    @patch("app.services.authorization_service.AuthorizationRepository.get_user_roles")
    async def test_get_user_role_names_success(self, mock_get_roles):
        """Тест получения списка ролей пользователя"""
        # Создаем mock роли
        role1 = MagicMock()
        role1.name = "user"
        role2 = MagicMock()
        role2.name = "moderator"

        mock_get_roles.return_value = [role1, role2]

        session = AsyncMock()
        result = await AuthorizationService.get_user_role_names(session, user_id=1)

        assert result == ["user", "moderator"]
        mock_get_roles.assert_called_once_with(session, 1)

    @patch("app.services.authorization_service.AuthorizationRepository.get_user_roles")
    async def test_get_user_role_names_empty(self, mock_get_roles):
        """Тест когда у пользователя нет ролей"""
        mock_get_roles.return_value = []

        session = AsyncMock()
        result = await AuthorizationService.get_user_role_names(session, user_id=1)

        assert result == []

    @patch("app.services.authorization_service.AuthorizationRepository.create_user_role")
    @patch("app.services.authorization_service.AuthorizationRepository.get_user_role_link")
    @patch("app.services.authorization_service.AuthorizationRepository.get_role_by_name")
    async def test_assign_role_to_user_success(
            self, mock_get_role, mock_get_link, mock_create_link
    ):
        """Тест успешного назначения роли пользователю"""
        mock_role = MagicMock()
        mock_role.id = 2
        mock_get_role.return_value = mock_role

        mock_get_link.return_value = None  # Роль еще не назначена
        mock_create_link.return_value = MagicMock()

        session = AsyncMock()
        result = await AuthorizationService.assign_role_to_user(
            session, user_id=1, role_name="moderator"
        )

        assert result is True
        mock_get_role.assert_called_once_with(session, "moderator")
        mock_get_link.assert_called_once_with(session, 1, 2)
        mock_create_link.assert_called_once_with(session, 1, 2)

    @patch("app.services.authorization_service.AuthorizationRepository.get_role_by_name")
    async def test_assign_role_to_user_role_not_found(self, mock_get_role):
        """Тест когда роль не найдена"""
        mock_get_role.return_value = None

        session = AsyncMock()
        result = await AuthorizationService.assign_role_to_user(
            session, user_id=1, role_name="nonexistent_role"
        )

        assert result is False
        mock_get_role.assert_called_once_with(session, "nonexistent_role")

    @patch("app.services.authorization_service.AuthorizationRepository.get_user_role_link")
    @patch("app.services.authorization_service.AuthorizationRepository.get_role_by_name")
    async def test_assign_role_to_user_already_has_role(
            self, mock_get_role, mock_get_link
    ):
        """Тест когда пользователь уже имеет эту роль"""
        mock_role = MagicMock()
        mock_role.id = 1
        mock_get_role.return_value = mock_role

        mock_get_link.return_value = MagicMock()  # Роль уже назначена

        session = AsyncMock()
        result = await AuthorizationService.assign_role_to_user(
            session, user_id=1, role_name="user"
        )

        assert result is True  # Возвращает True даже если роль уже есть
        mock_get_link.assert_called_once_with(session, 1, 1)

    @patch("app.services.authorization_service.AuthorizationRepository.create_user_role")
    @patch("app.services.authorization_service.AuthorizationRepository.get_user_role_link")
    @patch("app.services.authorization_service.AuthorizationRepository.get_role_by_name")
    async def test_assign_role_to_user_database_error(
            self, mock_get_role, mock_get_link, mock_create_link
    ):
        """Тест обработки ошибки базы данных при назначении роли"""
        mock_role = MagicMock()
        mock_role.id = 2
        mock_get_role.return_value = mock_role
        mock_get_link.return_value = None

        mock_create_link.side_effect = Exception("DB error")

        session = AsyncMock()
        result = await AuthorizationService.assign_role_to_user(
            session, user_id=1, role_name="moderator"
        )

        assert result is False