from unittest.mock import patch, AsyncMock

import pytest

from app.core.security import AuthService


@pytest.mark.asyncio
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

    @patch("app.core.redis.redis_manager.is_available")
    @patch("app.core.redis.redis_manager.get_client")
    async def test_add_to_blacklist_success(self, mock_get_client, mock_is_available):
        """Тест успешного добавления токена в blacklist"""
        mock_is_available.return_value = True
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.setex.return_value = True

        # Мокаем decode_token чтобы вернуть payload с expiration
        with patch.object(AuthService, 'decode_token') as mock_decode:
            mock_decode.return_value = {"exp": 9999999999, "type": "access"}

            result = await AuthService.add_to_blacklist("test_token", "access")

            assert result is True
            mock_client.setex.assert_called_once()

    @patch("app.core.redis.redis_manager.is_available")
    async def test_add_to_blacklist_redis_unavailable(self, mock_is_available):
        """Тест когда Redis недоступен"""
        mock_is_available.return_value = False

        result = await AuthService.add_to_blacklist("test_token", "access")

        assert result is False

    @patch("app.core.redis.redis_manager.is_available")
    @patch("app.core.redis.redis_manager.get_client")
    async def test_is_token_revoked_true(self, mock_get_client, mock_is_available):
        """Тест когда токен в blacklist"""
        mock_is_available.return_value = True
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.exists.return_value = 1  # Redis возвращает 1 если ключ существует

        result = await AuthService.is_token_revoked("test_token", "access")

        assert result is True

    @patch("app.core.redis.redis_manager.is_available")
    @patch("app.core.redis.redis_manager.get_client")
    async def test_is_token_revoked_false(self, mock_get_client, mock_is_available):
        """Тест когда токен НЕ в blacklist"""
        mock_is_available.return_value = True
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.exists.return_value = 0  # Redis возвращает 0 если ключа нет

        result = await AuthService.is_token_revoked("test_token", "access")

        assert result is False
