"""Tests for mode switching (mono <-> multi) endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.config import AppConfig
from app.models.user import User


class TestSwitchToMulti:
    @patch("app.api.admin.migrate_sqlite_to_postgres")
    @patch("app.api.admin.reset_engine")
    @patch("app.api.admin.save_app_config")
    @patch("app.api.admin.init_postgres_database")
    @patch("app.api.admin.test_database_connection", return_value=(True, "OK"))
    @patch("app.database.get_session_factory")
    def test_switch_to_multi_from_mono(
        self,
        mock_factory,
        mock_test_conn,
        mock_init_pg,
        mock_save,
        mock_reset,
        mock_migrate,
        multi_client: TestClient,
        admin_user: User,
        admin_token: str,
    ):
        """Switching from mono to multi succeeds when connection is valid."""
        mono_config = AppConfig(
            mode="mono",
            database_url="sqlite:///test.db",
            setup_completed=True,
            secret_key="a" * 64,
        )

        # Mock session factory to avoid real DB interaction
        mock_session = MagicMock()
        mock_factory.return_value = lambda: mock_session
        mock_migrate.return_value = {"documents": 2, "templates": 1}

        with patch("app.api.admin.get_app_config", return_value=mono_config):
            resp = multi_client.post(
                "/api/admin/switch-to-multi",
                json={
                    "pg_host": "localhost",
                    "pg_port": 5432,
                    "pg_user": "postgres",
                    "pg_password": "postgres",
                    "pg_database": "tabula",
                    "admin_username": "admin",
                    "admin_password": "adminpass",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["mode"] == "multi"
        mock_save.assert_called_once()

    def test_switch_to_multi_already_multi(
        self,
        multi_client: TestClient,
        admin_user: User,
        admin_token: str,
    ):
        """Switching to multi when already multi returns 400."""
        resp = multi_client.post(
            "/api/admin/switch-to-multi",
            json={
                "pg_host": "localhost",
                "pg_port": 5432,
                "pg_user": "postgres",
                "pg_password": "postgres",
                "pg_database": "tabula",
                "admin_username": "admin",
                "admin_password": "adminpass",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400
        assert "Already in multi" in resp.json()["detail"]

    @patch("app.api.admin.test_database_connection", return_value=(False, "Connection refused"))
    def test_switch_to_multi_bad_connection(
        self,
        mock_test_conn,
        multi_client: TestClient,
        admin_user: User,
        admin_token: str,
    ):
        """Switching to multi with bad PG connection returns 400."""
        mono_config = AppConfig(
            mode="mono",
            database_url="sqlite:///test.db",
            setup_completed=True,
            secret_key="a" * 64,
        )
        with patch("app.api.admin.get_app_config", return_value=mono_config):
            resp = multi_client.post(
                "/api/admin/switch-to-multi",
                json={
                    "pg_host": "badhost",
                    "pg_port": 5432,
                    "pg_user": "postgres",
                    "pg_password": "postgres",
                    "pg_database": "tabula",
                    "admin_username": "admin",
                    "admin_password": "adminpass",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        assert resp.status_code == 400
        assert "Cannot connect" in resp.json()["detail"]


class TestSwitchToMono:
    @patch("app.api.admin.reset_engine")
    @patch("app.api.admin.save_app_config")
    @patch("app.api.admin.migrate_postgres_to_sqlite")
    @patch("app.api.admin.init_sqlite_database")
    def test_switch_to_mono_from_multi(
        self,
        mock_init_sqlite,
        mock_migrate,
        mock_save,
        mock_reset,
        multi_client: TestClient,
        admin_user: User,
        admin_token: str,
    ):
        """Switching from multi to mono succeeds."""
        mock_migrate.return_value = {"documents": 3, "templates": 1}

        resp = multi_client.post(
            "/api/admin/switch-to-mono",
            json={
                "source_user_id": str(admin_user.id),
                "include_all_users": True,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["mode"] == "mono"
        mock_save.assert_called_once()

    def test_switch_to_mono_already_mono(
        self,
        multi_client: TestClient,
        admin_user: User,
        admin_token: str,
    ):
        """Switching to mono when already mono returns 400."""
        mono_config = AppConfig(
            mode="mono",
            database_url="sqlite:///test.db",
            setup_completed=True,
            secret_key="a" * 64,
        )
        with patch("app.api.admin.get_app_config", return_value=mono_config):
            resp = multi_client.post(
                "/api/admin/switch-to-mono",
                json={
                    "source_user_id": str(admin_user.id),
                    "include_all_users": True,
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        assert resp.status_code == 400
        assert "Already in mono" in resp.json()["detail"]
