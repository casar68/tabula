"""Tests for authentication utilities and endpoints."""

import uuid
from unittest.mock import patch

from app.config import AppConfig
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        plain = "my_secure_password"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed)

    def test_wrong_password(self):
        hashed = hash_password("correct_password")
        assert not verify_password("wrong_password", hashed)


class TestJWT:
    def setup_method(self):
        self.config = AppConfig(
            mode="multi",
            database_url="sqlite://",
            setup_completed=True,
            secret_key="test-jwt-secret-key-12345",
        )
        self.patcher = patch("app.core.auth.get_app_config", return_value=self.config)
        self.patcher.start()

    def teardown_method(self):
        self.patcher.stop()

    def test_access_token_roundtrip(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "testuser")
        payload = decode_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"

    def test_refresh_token_roundtrip(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_invalid_token(self):
        import jwt

        try:
            decode_token("invalid.token.string")
            assert False, "Should have raised"
        except jwt.PyJWTError:
            pass


class TestAuthEndpoints:
    """Test the auth API endpoints via the test client."""

    def _multi_config(self):
        return AppConfig(
            mode="multi",
            database_url="sqlite://",
            setup_completed=True,
            secret_key="test-secret-key-for-jwt",
            allow_registration=True,
        )

    def test_login_mono_mode_rejected(self, client):
        """Login should be rejected in mono mode."""
        resp = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "password",
        })
        assert resp.status_code == 400

    def test_register_mono_mode_rejected(self, client):
        """Registration should be rejected in mono mode."""
        resp = client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "password123",
        })
        assert resp.status_code == 400

    def test_register_and_login(self, client, db_session):
        """Full register + login flow in multi mode."""
        config = self._multi_config()
        with patch("app.config.get_app_config", return_value=config), \
             patch("app.core.dependencies.is_multi_user", return_value=True), \
             patch("app.api.auth.is_multi_user", return_value=True), \
             patch("app.api.auth.get_app_config", return_value=config):

            # Register
            resp = client.post("/api/auth/register", json={
                "username": "alice",
                "password": "password123",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["username"] == "alice"
            assert data["is_admin"] is False

            # Login
            resp = client.post("/api/auth/login", json={
                "username": "alice",
                "password": "password123",
            })
            assert resp.status_code == 200
            tokens = resp.json()
            assert "access_token" in tokens
            assert "refresh_token" in tokens

            # Get me
            resp = client.get("/api/auth/me", headers={
                "Authorization": f"Bearer {tokens['access_token']}",
            })
            assert resp.status_code == 200
            me = resp.json()
            assert me["username"] == "alice"

    def test_login_invalid_credentials(self, client, db_session):
        """Login with wrong credentials returns 401."""
        config = self._multi_config()
        with patch("app.config.get_app_config", return_value=config), \
             patch("app.core.dependencies.is_multi_user", return_value=True), \
             patch("app.api.auth.is_multi_user", return_value=True):

            resp = client.post("/api/auth/login", json={
                "username": "nonexistent",
                "password": "wrong",
            })
            assert resp.status_code == 401

    def test_duplicate_registration(self, client, db_session):
        """Registering twice with same username fails."""
        config = self._multi_config()
        with patch("app.config.get_app_config", return_value=config), \
             patch("app.core.dependencies.is_multi_user", return_value=True), \
             patch("app.api.auth.is_multi_user", return_value=True), \
             patch("app.api.auth.get_app_config", return_value=config):

            client.post("/api/auth/register", json={
                "username": "bob",
                "password": "password123",
            })
            resp = client.post("/api/auth/register", json={
                "username": "bob",
                "password": "password456",
            })
            assert resp.status_code == 409
