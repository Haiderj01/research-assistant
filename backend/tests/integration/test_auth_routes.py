from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import jwt as pyjwt
import pytest
from backend.app import create_app
from backend.services import auth_service

TEST_SECRET = "test-secret-key-for-integration-tests"


@pytest.fixture(autouse=True)
def set_secret(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "JWT_SECRET_KEY", TEST_SECRET)


@pytest.fixture(autouse=True)
def mock_domain(monkeypatch):
    monkeypatch.setattr(auth_service, "_domain_has_mail_records", lambda domain: True)


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def _register(client, email="new@example.com", password="password123", name="Ada Lovelace"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": name},
    )


class TestRegister:
    def test_register_success(self, client):
        resp = _register(client)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert "token" in body["data"]
        assert body["data"]["user"]["email"] == "new@example.com"
        assert body["data"]["user"]["name"] == "Ada Lovelace"

    def test_register_optional_name(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "noname@example.com", "password": "password123"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["data"]["user"]["name"] == ""

    def test_register_duplicate_email(self, client):
        _register(client)
        resp = _register(client)
        assert resp.status_code == 409
        body = resp.get_json()
        assert body["success"] is False
        assert body["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

    def test_register_invalid_json(self, client):
        resp = client.post("/api/v1/auth/register", data="not-json", content_type="application/json")
        assert resp.status_code == 400

    def test_register_disposable_email(self, client):
        resp = _register(client, email="user@mailinator.com")
        assert resp.status_code == 422
        assert resp.get_json()["error"]["code"] == "DISPOSABLE_EMAIL"

    def test_register_domain_without_mail_records(self, client, monkeypatch):
        monkeypatch.setattr(
            auth_service, "_domain_has_mail_records", lambda domain: False
        )
        resp = _register(client, email="user@nonexistent-domain-xyz.com")
        assert resp.status_code == 422
        assert resp.get_json()["error"]["code"] == "INVALID_EMAIL_DOMAIN"


class TestLogin:
    def test_login_success(self, client):
        _register(client)
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "new@example.com", "password": "password123"},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "token" in body["data"]

    def test_login_wrong_password(self, client):
        _register(client)
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "new@example.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_unknown_email(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "password123"},
        )
        assert resp.status_code == 401


class TestProtectedRoutes:
    def test_health_is_public(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_protected_route_without_token(self, client):
        resp = client.get("/api/v1/papers")
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"

    def test_protected_route_with_valid_token(self, client):
        token = auth_service.generate_token("507f1f77bcf86cd799439011")
        resp = client.get(
            "/api/v1/papers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_protected_route_with_invalid_token(self, client):
        resp = client.get(
            "/api/v1/papers",
            headers={"Authorization": "Bearer not.a.jwt"},
        )
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "INVALID_TOKEN"

    def test_protected_route_with_expired_token(self, client):
        now = datetime.now(timezone.utc)
        token = pyjwt.encode(
            {"sub": "abc", "iat": now - timedelta(days=8), "exp": now - timedelta(days=1)},
            TEST_SECRET,
            algorithm="HS256",
        )
        resp = client.get(
            "/api/v1/papers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "TOKEN_EXPIRED"

    def test_register_login_token_works_on_protected_route(self, client):
        reg = _register(client, email="flow@example.com", password="password123")
        token = reg.get_json()["data"]["token"]
        resp = client.get(
            "/api/v1/papers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
