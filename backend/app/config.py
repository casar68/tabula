"""Application configuration.

Two layers:
- ``Settings`` (env vars / .env): immutable infrastructure settings
- ``AppConfig`` (tabula.config.json): mutable runtime config persisted to disk
"""

import json
import secrets
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Environment-based settings (read-only at runtime)."""

    # Storage
    data_dir: Path = Path(__file__).parent.parent / "data"
    upload_dir: Path = Path(__file__).parent.parent / "uploads"

    # App
    app_name: str = "Tabula"
    app_version: str = "2.0.0"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]  # Vite dev server

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8"}


settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.upload_dir.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Persistent application configuration (stored in tabula.config.json)
# ---------------------------------------------------------------------------

_CONFIG_FILE_NAME = "tabula.config.json"


class AppConfig(BaseModel):
    """Persisted application configuration (JSON file)."""

    mode: str = "mono"  # "mono" or "multi"
    database_url: str = ""  # filled at setup time
    secret_key: str = ""  # JWT signing key, generated once
    allow_registration: bool = True
    setup_completed: bool = False


# In-memory cache to avoid reading and parsing the JSON file on every request.
# Thread-safe: Python's GIL guarantees atomic assignment; AppConfig instances
# are effectively immutable after creation.
_cached_config: AppConfig | None = None


def _config_path() -> Path:
    return settings.data_dir / _CONFIG_FILE_NAME


def get_app_config() -> AppConfig:
    """Load config from cache, disk, or return defaults."""
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    path = _config_path()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        _cached_config = AppConfig(**data)
        return _cached_config

    # No config file yet -- return defaults with SQLite URL.
    # Do NOT cache defaults so that subsequent calls can detect the file
    # once it has been written by the setup wizard.
    default_db = f"sqlite:///{settings.data_dir / 'tabula.db'}"
    return AppConfig(database_url=default_db)


def save_app_config(config: AppConfig) -> None:
    """Persist config to disk and update in-memory cache."""
    global _cached_config
    path = _config_path()
    path.write_text(
        json.dumps(config.model_dump(), indent=2),
        encoding="utf-8",
    )
    _cached_config = config


def invalidate_config_cache() -> None:
    """Clear the in-memory config cache, forcing a re-read on next access."""
    global _cached_config
    _cached_config = None


def is_setup_completed() -> bool:
    return get_app_config().setup_completed


def is_multi_user() -> bool:
    cfg = get_app_config()
    return cfg.mode == "multi"


def ensure_secret_key(config: AppConfig) -> AppConfig:
    """Generate a secret_key if not already set."""
    if not config.secret_key:
        config.secret_key = secrets.token_hex(32)
    return config
