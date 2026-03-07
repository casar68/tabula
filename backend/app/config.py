from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/nkf"

    # Storage
    upload_dir: Path = Path(__file__).parent.parent / "uploads"

    # App
    app_name: str = "Tabula"
    app_version: str = "2.0.0"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]  # Vite dev server

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8"}


settings = Settings()

# Ensure upload directory exists
settings.upload_dir.mkdir(parents=True, exist_ok=True)
