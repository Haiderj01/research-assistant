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
        patch("backend.services.auth_service._domain_has_mail_records", return_value=True) as mock_domain,
    ):
        mock_bcrypt.hashpw.return_value = b"$2b$12$hashedpasswordvalue"
        mock_bcrypt.checkpw.return_value = True
        yield {
            "user_model": mock_user,
            "bcrypt": mock_bcrypt,
            "domain": mock_domain,
        }


@pytest.fixture(autouse=True)
def set_secret(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "JWT_SECRET_KEY", TEST_SECRET)


def _user(email="test@example.com", uid="507f1f77bcf86cd799439011", name=""):
    return {
        "_id": uid,
        "email": email,
        "name": name,
        "password_hash": "$2b$12$hashedpasswordvalue",
        "created_at": datetime.now(timezone.utc),
    }


class TestRegisterUser:
    def test_register_success(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = None
        mock_deps["user_model"].create_user.return_value = _user(name="Ada Lovelace")

        result = auth_service.register_user("test@example.com", "password123", "Ada Lovelace")

        assert "token" in result
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["name"] == "Ada Lovelace"
        mock_deps["user_model"].create_user.assert_called_once_with(
            "test@example.com", "$2b$12$hashedpasswordvalue", "Ada Lovelace"
        )

    def test_register_stores_optional_name(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = None
        mock_deps["user_model"].create_user.return_value = _user(name="")

        auth_service.register_user("test@example.com", "password123", "  Jane  ")

        args, _ = mock_deps["user_model"].create_user.call_args
        assert args[2] == "Jane"

    def test_register_empty_name(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = None
        mock_deps["user_model"].create_user.return_value = _user()

        auth_service.register_user("test@example.com", "password123")

        args, _ = mock_deps["user_model"].create_user.call_args
        assert args[2] == ""

    def test_register_name_too_long(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = None

        with pytest.raises(AppError) as exc:
            auth_service.register_user("test@example.com", "password123", "x" * 81)
        assert exc.value.status_code == 422
        assert exc.value.code == "INVALID_NAME"

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

    def test_register_disposable_email(self, mock_deps):
        with pytest.raises(AppError) as exc:
            auth_service.register_user("user@mailinator.com", "password123")
        assert exc.value.status_code == 422
        assert exc.value.code == "DISPOSABLE_EMAIL"
        mock_deps["domain"].assert_not_called()

    def test_register_domain_without_mail_records(self, mock_deps):
        mock_deps["domain"].return_value = False
        with pytest.raises(AppError) as exc:
            auth_service.register_user("user@nonexistent-domain-xyz.com", "password123")
        assert exc.value.status_code == 422
        assert exc.value.code == "INVALID_EMAIL_DOMAIN"

    def test_register_checks_domain_dns(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = None
        mock_deps["user_model"].create_user.return_value = _user()

        auth_service.register_user("test@example.com", "password123")

        mock_deps["domain"].assert_called_once_with("example.com")


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


class TestGoogleOAuth:
    def test_google_new_user_creates_google_account(self, mock_deps):
        mock_deps["user_model"].get_user_by_email.return_value = None
        mock_deps["user_model"].create_user.return_value = _user(email="ada@example.com", name="Ada Lovelace")

        result = auth_service.login_or_register_google({"email": "ada@example.com", "name": "Ada Lovelace"})

        assert result["created"] is True
        assert result["user"]["email"] == "ada@example.com"
        assert result["user"]["name"] == "Ada Lovelace"
        assert "token" in result
        mock_deps["user_model"].create_user.assert_called_once_with(
            "ada@example.com", None, "Ada Lovelace", auth_provider="google"
        )

    def test_google_existing_email_logs_into_same_account(self, mock_deps):
        existing = _user(email="ada@example.com", name="Ada")
        mock_deps["user_model"].get_user_by_email.return_value = existing

        result = auth_service.login_or_register_google({"email": "ada@example.com", "name": "Ada Lovelace"})

        assert result["created"] is False
        assert result["user"]["id"] == "507f1f77bcf86cd799439011"
        assert result["user"]["email"] == "ada@example.com"
        mock_deps["user_model"].create_user.assert_not_called()

    def test_google_user_cannot_password_login(self, mock_deps):
        google_user = _user(email="ada@example.com")
        google_user["password_hash"] = None
        mock_deps["user_model"].get_user_by_email.return_value = google_user

        with pytest.raises(AppError) as exc:
            auth_service.login_user("ada@example.com", "anything123")
        assert exc.value.status_code == 401
        assert exc.value.code == "INVALID_CREDENTIALS"
        mock_deps["bcrypt"].checkpw.assert_not_called()

    def test_google_auth_url_contains_required_params(self):
        url = auth_service.google_auth_url("http://localhost:5003/api/v1/auth/google/callback")

        assert url.startswith(auth_service.GOOGLE_AUTH_ENDPOINT + "?")
        assert "client_id=" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%3A5003%2Fapi%2Fv1%2Fauth%2Fgoogle%2Fcallback" in url
        assert "response_type=code" in url
        assert "scope=openid+email+profile" in url
        assert "state=" in url

    def test_oauth_state_roundtrip(self):
        state = auth_service._oauth_state()
        auth_service.verify_oauth_state(state)  # should not raise

    def test_oauth_state_rejects_garbage(self):
        with pytest.raises(AppError) as exc:
            auth_service.verify_oauth_state("not-a-real-state")
        assert exc.value.status_code == 400
        assert exc.value.code == "INVALID_OAUTH_STATE"
