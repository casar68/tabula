"""Schemas for admin mode switching."""

import uuid

from pydantic import BaseModel, Field


class SwitchToMultiRequest(BaseModel):
    """Switch from mono to multi-user mode."""

    pg_host: str
    pg_port: int = 5432
    pg_user: str
    pg_password: str
    pg_database: str
    admin_username: str = Field(..., min_length=3, max_length=150)
    admin_password: str = Field(..., min_length=6)
    migrate_data: bool = True  # migrate existing SQLite data to admin account


class SwitchToMonoRequest(BaseModel):
    """Switch from multi to mono-user mode."""

    source_user_id: uuid.UUID  # user whose documents to keep
    include_all_users: bool = False  # if True, keep all users' documents


class SwitchModeResponse(BaseModel):
    success: bool
    mode: str
    message: str
    migrated: dict | None = None  # {"documents": N, "templates": N}
