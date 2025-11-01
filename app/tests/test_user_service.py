import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.user_service import UserService
from app.core.security import AuthService
from app.core.exceptions import UserAlreadyExistsException, InvalidCredentialsException
from app.api.v1.schemas import UserUpdate


@pytest.mark.asyncio
class TestUserService:

    @patch("app.services.user_service.UserRepository.get_user_by_email")
    async def test_authenticate_user_success(self, mock_get_user, mock_user):
        mock_get_user.return_value = mock_user

        with patch.object(AuthService, "verify_password", return_value=True):
            session = AsyncMock()
            result = await UserService.authenticate_user(
                session, "test@example.com", "correct_password"
            )
            assert result == mock_user

    @patch("app.services.user_service.UserRepository.get_user_by_email")
    async def test_authenticate_user_wrong_password(self, mock_get_user, mock_user):
        mock_get_user.return_value = mock_user

        with patch.object(AuthService, "verify_password", return_value=False):
            session = AsyncMock()
            with pytest.raises(InvalidCredentialsException):
                await UserService.authenticate_user(
                    session, "test@example.com", "wrong_password"
                )

    @patch("app.services.user_service.UserRepository.get_user_by_email")
    async def test_authenticate_user_not_found(self, mock_get_user):
        mock_get_user.return_value = None

        session = AsyncMock()
        with pytest.raises(InvalidCredentialsException):
            await UserService.authenticate_user(
                session, "nonexistent@example.com", "password"
            )

    @patch("app.services.user_service.AuthorizationService.assign_role_to_user")
    @patch("app.services.user_service.UserRepository.create_user")
    @patch("app.services.user_service.UserRepository.get_user_by_email")
    async def test_create_user_success(
            self, mock_get_user, mock_create_user, mock_assign_role, mock_user
    ):
        mock_get_user.return_value = None  # Пользователь не существует
        mock_create_user.return_value = mock_user
        mock_assign_role.return_value = True

        session = AsyncMock()
        result = await UserService.create_user(
            session,
            username="testuser",
            email="test@example.com",
            first_name="Ivan",
            last_name="Petrov",
            middle_name="Sergeevich",
            hashed_password="hashed_password_123"
        )

        assert result == mock_user
        mock_create_user.assert_called_once()
        mock_assign_role.assert_called_once_with(session, mock_user.id, "user")
        session.commit.assert_called_once()

    @patch("app.services.user_service.UserRepository.get_user_by_email")
    async def test_create_user_email_exists(self, mock_get_user, mock_user):
        mock_get_user.return_value = mock_user  # Пользователь уже существует

        session = AsyncMock()
        with pytest.raises(UserAlreadyExistsException):
            await UserService.create_user(
                session,
                username="testuser",
                email="test@example.com",
                first_name="Ivan",
                last_name="Petrov",
                middle_name="Sergeevich",
                hashed_password="hashed_password_123"
            )

    @patch("app.services.user_service.AuthorizationService.assign_role_to_user")
    @patch("app.services.user_service.UserRepository.create_user")
    @patch("app.services.user_service.UserRepository.get_user_by_email")
    async def test_create_user_rollback_on_error(
            self, mock_get_user, mock_create_user, mock_assign_role
    ):
        mock_get_user.return_value = None
        mock_create_user.side_effect = Exception("DB error")

        session = AsyncMock()
        with pytest.raises(Exception):
            await UserService.create_user(
                session,
                username="testuser",
                email="test@example.com",
                first_name="Ivan",
                last_name="Petrov",
                middle_name="Sergeevich",
                hashed_password="hashed_password_123"
            )

        session.rollback.assert_called_once()

    @patch("app.services.user_service.UserRepository.get_user_by_email")
    async def test_update_user_success(self, mock_get_user, mock_user):
        mock_get_user.return_value = None  # Email свободен

        session = AsyncMock()
        user_data = UserUpdate(
            username="newusername",
            email="new@example.com",
            first_name="NewName",
            last_name="NewLastName",
            middle_name="NewMiddleName"
        )

        # Исходный пользователь
        original_user = MagicMock()
        original_user.id = 1
        original_user.username = "oldusername"
        original_user.email = "old@example.com"
        original_user.first_name = "OldName"
        original_user.last_name = "OldLastName"
        original_user.middle_name = "OldMiddleName"

        result = await UserService.update_user(session, original_user, user_data)

        # Проверяем что поля обновились
        assert original_user.username == "newusername"
        assert original_user.email == "new@example.com"
        assert original_user.first_name == "NewName"
        session.commit.assert_called_once()
        session.refresh.assert_called_once_with(original_user)

    @patch("app.services.user_service.UserRepository.get_user_by_email")
    async def test_update_user_email_conflict(self, mock_get_user, mock_user):
        # Другой пользователь уже использует этот email
        mock_get_user.return_value = MagicMock(id=999)

        session = AsyncMock()
        user_data = UserUpdate(email="existing@example.com")

        current_user = MagicMock()
        current_user.id = 1
        current_user.email = "current@example.com"

        with pytest.raises(UserAlreadyExistsException):
            await UserService.update_user(session, current_user, user_data)

    async def test_update_user_partial_data(self, mock_user):
        session = AsyncMock()
        user_data = UserUpdate(first_name="OnlyFirstName")  # Только одно поле

        original_user = MagicMock()
        original_user.id = 1
        original_user.first_name = "OldFirstName"
        original_user.last_name = "OldLastName"

        result = await UserService.update_user(session, original_user, user_data)

        assert original_user.first_name == "OnlyFirstName"
        assert original_user.last_name == "OldLastName"  # Не изменилось
        session.commit.assert_called_once()


    async def test_deactivate_user_success(self, mock_user):
        session = AsyncMock()

        mock_user.is_active = True  # Изначально активен
        await UserService.deactivate_user(session, mock_user)

        assert mock_user.is_active is False
        session.commit.assert_called_once()