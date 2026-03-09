"""Tests for the AppConfig system."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from app.config import (
    AppConfig,
    ensure_secret_key,
    get_app_config,
    invalidate_config_cache,
    save_app_config,
)


class TestAppConfig:
    def test_defaults(self):
        config = AppConfig()
        assert config.mode == "mono"
        assert config.database_url == ""
        assert config.setup_completed is False
        assert config.allow_registration is True

    def test_ensure_secret_key_generates(self):
        config = AppConfig()
        assert config.secret_key == ""
        config = ensure_secret_key(config)
        assert len(config.secret_key) == 64  # hex of 32 bytes

    def test_ensure_secret_key_preserves(self):
        config = AppConfig(secret_key="existing-key")
        config = ensure_secret_key(config)
        assert config.secret_key == "existing-key"


class TestConfigPersistence:
    def setup_method(self):
        invalidate_config_cache()

    def teardown_method(self):
        invalidate_config_cache()

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = AppConfig(
                mode="multi",
                database_url="postgresql://localhost/test",
                setup_completed=True,
                secret_key="my-secret",
            )

            config_path = Path(tmp_dir) / "tabula.config.json"
            with patch("app.config._config_path", return_value=config_path):
                save_app_config(config)
                loaded = get_app_config()

            assert loaded.mode == "multi"
            assert loaded.database_url == "postgresql://localhost/test"
            assert loaded.setup_completed is True
            assert loaded.secret_key == "my-secret"

    def test_no_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "nonexistent.json"
            with patch("app.config._config_path", return_value=config_path), \
                 patch("app.config.settings") as mock_settings:
                mock_settings.data_dir = Path(tmp_dir)
                config = get_app_config()

            assert config.mode == "mono"
            assert config.setup_completed is False
            assert "sqlite" in config.database_url


class TestConfigCache:
    def setup_method(self):
        invalidate_config_cache()

    def teardown_method(self):
        invalidate_config_cache()

    def test_cache_returns_same_object(self):
        """Two consecutive calls return the exact same object (identity)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "tabula.config.json"
            config = AppConfig(mode="mono", database_url="sqlite:///test.db",
                               setup_completed=True)
            with patch("app.config._config_path", return_value=config_path):
                save_app_config(config)
                first = get_app_config()
                second = get_app_config()
            assert first is second

    def test_save_updates_cache(self):
        """After save_app_config(), get_app_config() returns updated values."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "tabula.config.json"
            with patch("app.config._config_path", return_value=config_path):
                original = AppConfig(mode="mono", database_url="sqlite:///a.db",
                                     setup_completed=True)
                save_app_config(original)

                updated = AppConfig(mode="multi", database_url="postgresql://x",
                                    setup_completed=True, secret_key="s")
                save_app_config(updated)

                loaded = get_app_config()
            assert loaded.mode == "multi"
            assert loaded.database_url == "postgresql://x"
            assert loaded is updated  # same cached object

    def test_invalidate_forces_reread(self):
        """After invalidate_config_cache(), the file is read again."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "tabula.config.json"
            with patch("app.config._config_path", return_value=config_path):
                config = AppConfig(mode="mono", database_url="sqlite:///test.db",
                                   setup_completed=True)
                save_app_config(config)
                first = get_app_config()

                invalidate_config_cache()

                second = get_app_config()
            # Same values but different objects (re-read from disk)
            assert first is not second
            assert first.mode == second.mode

    def test_defaults_not_cached(self):
        """When the config file doesn't exist, defaults are NOT cached."""
        import app.config as cfg_mod

        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "nonexistent.json"
            with patch("app.config._config_path", return_value=config_path), \
                 patch("app.config.settings") as mock_settings:
                mock_settings.data_dir = Path(tmp_dir)
                get_app_config()
                assert cfg_mod._cached_config is None
