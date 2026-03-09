"""Tests for the setup wizard API."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from app.config import AppConfig


class TestSetupStatus:
    def test_setup_not_completed(self, client):
        """When config shows setup not completed, status reflects it."""
        config = AppConfig(
            mode="mono",
            database_url="sqlite://",
            setup_completed=False,
        )
        with patch("app.api.setup.get_app_config", return_value=config):
            resp = client.get("/api/setup/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["setup_completed"] is False
            assert data["mode"] is None

    def test_setup_completed(self, client):
        """When setup is completed, status includes the mode."""
        config = AppConfig(
            mode="mono",
            database_url="sqlite://",
            setup_completed=True,
        )
        with patch("app.api.setup.get_app_config", return_value=config):
            resp = client.get("/api/setup/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["setup_completed"] is True
            assert data["mode"] == "mono"


class TestInitMono:
    def test_init_mono_succeeds(self, client):
        """Setting up mono mode creates SQLite and marks setup complete."""
        config = AppConfig(
            mode="mono",
            database_url="sqlite://",
            setup_completed=False,
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("app.api.setup.get_app_config", return_value=config), \
                 patch("app.api.setup.settings") as mock_settings, \
                 patch("app.api.setup.save_app_config") as mock_save, \
                 patch("app.api.setup.reset_engine"), \
                 patch("app.api.setup.init_sqlite_database"):

                mock_settings.data_dir = Path(tmp_dir)

                resp = client.post("/api/setup/init", json={"mode": "mono"})
                assert resp.status_code == 200
                data = resp.json()
                assert data["success"] is True
                assert data["mode"] == "mono"
                assert mock_save.called

    def test_init_when_already_completed(self, client):
        """Cannot re-init once setup is done."""
        config = AppConfig(
            mode="mono",
            database_url="sqlite://",
            setup_completed=True,
        )
        with patch("app.api.setup.get_app_config", return_value=config):
            resp = client.post("/api/setup/init", json={"mode": "mono"})
            assert resp.status_code == 400


class TestSetupGate:
    def test_gate_blocks_api_when_setup_not_completed(self, client):
        """API endpoints return 503 when setup is not completed."""
        with patch("app.main.is_setup_completed", return_value=False):
            resp = client.get("/api/documents")
            assert resp.status_code == 503
            data = resp.json()
            assert data["setup_required"] is True

    def test_gate_allows_setup_endpoints(self, client):
        """Setup endpoints are not blocked by the gate."""
        config = AppConfig(
            mode="mono",
            database_url="sqlite://",
            setup_completed=False,
        )
        with patch("app.main.is_setup_completed", return_value=False), \
             patch("app.api.setup.get_app_config", return_value=config):
            resp = client.get("/api/setup/status")
            assert resp.status_code == 200

    def test_gate_allows_settings_endpoint(self, client):
        """Settings endpoint is not blocked by the gate."""
        with patch("app.main.is_setup_completed", return_value=False):
            resp = client.get("/api/settings")
            assert resp.status_code == 200
