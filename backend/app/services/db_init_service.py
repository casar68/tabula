"""Database initialization service.

Handles creating tables for both SQLite (mono) and PostgreSQL (multi) modes.
"""

import logging

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool

# Ensure all models are registered on Base.metadata
import app.models.document  # noqa: F401
import app.models.job  # noqa: F401
import app.models.template  # noqa: F401
import app.models.user  # noqa: F401
from app.database import Base

logger = logging.getLogger(__name__)


def test_database_connection(url: str) -> tuple[bool, str]:
    """Test whether a database URL is reachable.

    Returns (success, message).
    """
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True, "Connection successful"
    except Exception as exc:
        return False, str(exc)


def init_sqlite_database(db_path: str) -> None:
    """Create all tables in a SQLite database file."""
    url = f"sqlite:///{db_path}"
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    engine.dispose()
    logger.info("SQLite database initialised at %s", db_path)


def init_postgres_database(url: str) -> None:
    """Create all tables in a PostgreSQL database.

    For a fresh install we use ``create_all`` directly.
    When Alembic migrations exist we could call ``alembic upgrade head``
    instead, but ``create_all`` is simpler for the initial setup.
    """
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    engine.dispose()
    logger.info("PostgreSQL database initialised")
