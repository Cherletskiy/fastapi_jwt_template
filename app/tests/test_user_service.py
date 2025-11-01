from unittest.mock import patch, AsyncMock

import pytest


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
