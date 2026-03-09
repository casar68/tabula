"""Schemas for the first-run setup wizard."""

from pydantic import BaseModel, Field


class SetupRequest(BaseModel):
    """Request to initialize the application mode."""

    mode: str = Field(..., pattern="^(mono|multi)$")

    # PostgreSQL connection (required when mode == "multi")
    pg_host: str | None = None
    pg_port: int = 5432
    pg_user: str | None = None
    pg_password: str | None = None
    pg_database: str | None = None

    # Admin account (required when mode == "multi")
    admin_username: str | None = None
    admin_password: str | None = None


class SetupStatusResponse(BaseModel):
    setup_completed: bool
    mode: str | None = None


class SetupResponse(BaseModel):
    success: bool
    mode: str
    message: str
