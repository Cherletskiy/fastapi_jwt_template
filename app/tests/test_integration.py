from unittest.mock import patch

from app.tests.conftest import client


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