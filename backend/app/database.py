"""Database engine and session management.

Supports lazy initialization to allow switching between SQLite and PostgreSQL
depending on the application configuration (mono vs multi-user mode).
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

_engine = None
_SessionLocal = None


class Base(DeclarativeBase):
    pass


def get_engine():
    """Get or create the SQLAlchemy engine (lazy initialization)."""
    global _engine
    if _engine is not None:
        return _engine

    from app.config import get_app_config

    config = get_app_config()
    db_url = config.database_url

    if db_url.startswith("sqlite"):
        _engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
    else:
        _engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )

    return _engine


def get_session_factory():
    """Get or create the session factory (lazy initialization)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return _SessionLocal


# Keep SessionLocal as a property-like access for backward compatibility
# (used by background threads in documents.py)
class _SessionLocalProxy:
    """Proxy that lazily creates the session factory."""

    def __call__(self):
        return get_session_factory()()


SessionLocal = _SessionLocalProxy()


def reset_engine():
    """Reset engine and session factory (used when switching modes)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a database session."""
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
