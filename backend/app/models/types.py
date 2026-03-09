"""Cross-database compatible SQLAlchemy types.

Provides UniversalUUID and UniversalJSON that work transparently
on both PostgreSQL (native UUID/JSONB) and SQLite (String/JSON).
"""

import uuid

from sqlalchemy import JSON, String, Text
from sqlalchemy.types import TypeDecorator

try:
    from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
except ImportError:  # pragma: no cover
    PG_UUID = None  # type: ignore[assignment, misc]
    PG_JSONB = None  # type: ignore[assignment, misc]


class UniversalUUID(TypeDecorator):
    """UUID type that uses native UUID on PostgreSQL, String(36) on SQLite."""

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PG_UUID is not None:
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value


class UniversalJSON(TypeDecorator):
    """JSON type that uses JSONB on PostgreSQL, JSON on SQLite."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PG_JSONB is not None:
            return dialect.type_descriptor(PG_JSONB(astext_type=Text()))
        return dialect.type_descriptor(JSON())
