import pytest

from app.core.security import AuthService


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
