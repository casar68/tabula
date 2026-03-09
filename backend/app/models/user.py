"""User model for multi-user mode."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import UniversalUUID


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships (back-populated by Document and Template in Phase 4)
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        back_populates="owner", lazy="dynamic"
    )
    templates: Mapped[list["Template"]] = relationship(  # noqa: F821
        back_populates="owner", lazy="dynamic"
    )

    def __repr__(self) -> str:
        role = "admin" if self.is_admin else "user"
        return f"<User {self.username} ({role})>"
