from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
import jwt as pyjwt

from backend.services import auth_service
from backend.middlewares.error_handler import AppError

TEST_SECRET = "test-secret-key-for-unit-tests"


@pytest.fixture(autouse=True)
def mock_deps():
    with (
        patch("backend.services.auth_service.user_model") as mock_user,
        patch("backend.services.auth_service.bcrypt") as mock_bcrypt,
    ):
        mock_bcrypt.hashpw.return_value = b"$2b$12$hashedpasswordvalue"
        mock_bcrypt.checkpw.return_value = True
        yield {
            "user_model": mock_user,
            "bcrypt": mock_bcrypt,
        }


@pytest.fixture(autouse=True)
def set_secret(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "JWT_SECRET_KEY", TEST_SECRET)


def _user(email="test@example.com", uid="507f1f77bcf86cd799439011"):
    return {
        "_id": uid,
        "email": email,
        "password_hash": "$2b$12$hashedpasswordvalue",
        "created_at": datetime.now(timezone.utc),
    }


class TestRegisterUser:
    def test_register_success(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = None
        mock_deps["user_model"].create_user.return_value = _user()

        result = auth_service.register_user("test@example.com", "password123")

        assert "token" in result
        assert result["user"]["email"] == "test@example.com"
        mock_deps["user_model"].create_user.assert_called_once()

    def test_register_normalizes_email(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = None
        mock_deps["user_model"].create_user.return_value = _user()

        auth_service.register_user("  Test@Example.COM ", "password123")

        args, _ = mock_deps["user_model"].create_user.call_args
        assert args[0] == "test@example.com"

    def test_register_duplicate_email(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = _user()

        with pytest.raises(AppError) as exc:
            auth_service.register_user("test@example.com", "password123")
        assert exc.value.status_code == 409
        assert exc.value.code == "EMAIL_ALREADY_REGISTERED"

    def test_register_weak_password(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = None

        with pytest.raises(AppError) as exc:
            auth_service.register_user("test@example.com", "short")
        assert exc.value.status_code == 422
        assert exc.value.code == "WEAK_PASSWORD"

    def test_register_invalid_email(self, mock_deps):
        with pytest.raises(AppError) as exc:
            auth_service.register_user("not-an-email", "password123")
        assert exc.value.status_code == 422
        assert exc.value.code == "INVALID_EMAIL"


class TestLoginUser:
    def test_login_success(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = _user()

        result = auth_service.login_user("test@example.com", "password123")

        assert "token" in result
        assert result["user"]["email"] == "test@example.com"
        mock_deps["bcrypt"].checkpw.assert_called_once()

    def test_login_wrong_password(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = _user()
        mock_deps["bcrypt"].checkpw.return_value = False

        with pytest.raises(AppError) as exc:
            auth_service.login_user("test@example.com", "wrongpassword")
        assert exc.value.status_code == 401
        assert exc.value.code == "INVALID_CREDENTIALS"
        assert "invalid email or password" in exc.value.message.lower()

    def test_login_unknown_email_generic_message(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = None

        with pytest.raises(AppError) as exc:
            auth_service.login_user("ghost@example.com", "password123")
        assert exc.value.status_code == 401
        assert "invalid email or password" in exc.value.message.lower()


class TestToken:
    def test_generate_and_verify_token(self):
        token = auth_service.generate_token("507f1f77bcf86cd799439011")
        assert auth_service.verify_token(token) == "507f1f77bcf86cd799439011"

    def test_verify_token_rejects_garbage(self):
        with pytest.raises(AppError) as exc:
            auth_service.verify_token("not.a.jwt")
        assert exc.value.status_code == 401
        assert exc.value.code == "INVALID_TOKEN"

    def test_verify_token_rejects_expired(self):
        now = datetime.now(timezone.utc)
        token = pyjwt.encode(
            {"sub": "abc", "iat": now - timedelta(days=8), "exp": now - timedelta(days=1)},
            TEST_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(AppError) as exc:
            auth_service.verify_token(token)
        assert exc.value.status_code == 401
        assert exc.value.code == "TOKEN_EXPIRED"

    def test_verify_token_rejects_missing(self):
        with pytest.raises(AppError) as exc:
            auth_service.verify_token("")
        assert exc.value.status_code == 401
