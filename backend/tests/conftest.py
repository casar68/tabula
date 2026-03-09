"""Shared test fixtures for backend tests."""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models so they register with Base.metadata BEFORE create_all().
import app.models.document  # noqa: F401
import app.models.job  # noqa: F401
import app.models.template  # noqa: F401
import app.models.user  # noqa: F401
from app.config import AppConfig, invalidate_config_cache, settings
from app.core.auth import create_access_token, hash_password
from app.database import Base, get_db
from app.models.user import User

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Secret key used across all test fixtures (32 bytes hex = 64 chars).
TEST_SECRET_KEY = "a" * 64


# ---------------------------------------------------------------------------
# SQLite in-memory database for tests
# ---------------------------------------------------------------------------
# UniversalUUID and UniversalJSON automatically use SQLite-compatible types,
# so no manual JSONB→JSON column swapping is needed.


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Create a fresh SQLite in-memory database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def mock_app_config():
    """Provide a default mono-mode AppConfig for tests.

    Must patch ``is_multi_user`` / ``is_setup_completed`` at every import site
    because ``from app.config import X`` creates a local reference that is not
    affected by patching the name in ``app.config``.
    """
    invalidate_config_cache()
    config = AppConfig(
        mode="mono",
        database_url="sqlite://",
        setup_completed=True,
        secret_key=TEST_SECRET_KEY,
    )
    with patch("app.config.get_app_config", return_value=config), \
         patch("app.core.dependencies.is_multi_user", return_value=False), \
         patch("app.api.auth.is_multi_user", return_value=False), \
         patch("app.main.is_setup_completed", return_value=True):
        yield config
    invalidate_config_cache()


@pytest.fixture()
def client(db_session: Session, mock_app_config) -> Generator:
    """FastAPI TestClient with overridden database dependency."""
    from fastapi.testclient import TestClient

    from app.main import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    # Use a temporary uploads directory
    tmp_dir = tempfile.mkdtemp()
    original_upload_dir = settings.upload_dir
    settings.upload_dir = Path(tmp_dir)

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
    settings.upload_dir = original_upload_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Multi-user mode fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def multi_config():
    """Provide a multi-user AppConfig for tests."""
    invalidate_config_cache()
    config = AppConfig(
        mode="multi",
        database_url="sqlite://",
        setup_completed=True,
        secret_key=TEST_SECRET_KEY,
        allow_registration=True,
    )
    with patch("app.config.get_app_config", return_value=config), \
         patch("app.config.is_multi_user", return_value=True), \
         patch("app.config.is_setup_completed", return_value=True):
        yield config
    invalidate_config_cache()


@pytest.fixture()
def admin_user(db_session: Session) -> User:
    """Create an admin user in the test database."""
    user = User(
        username="admin",
        password_hash=hash_password("adminpass"),
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def regular_user(db_session: Session) -> User:
    """Create a regular user (alice) in the test database."""
    user = User(
        username="alice",
        password_hash=hash_password("alicepass"),
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def second_user(db_session: Session) -> User:
    """Create a second regular user (bob) in the test database."""
    user = User(
        username="bob",
        password_hash=hash_password("bobpass"),
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_token(admin_user: User, multi_config) -> str:
    """JWT access token for the admin user."""
    return create_access_token(admin_user.id, admin_user.username)


@pytest.fixture()
def user_token(regular_user: User, multi_config) -> str:
    """JWT access token for alice."""
    return create_access_token(regular_user.id, regular_user.username)


@pytest.fixture()
def second_user_token(second_user: User, multi_config) -> str:
    """JWT access token for bob."""
    return create_access_token(second_user.id, second_user.username)


@pytest.fixture()
def multi_client(db_session: Session, multi_config) -> Generator:
    """FastAPI TestClient configured for multi-user mode."""
    from fastapi.testclient import TestClient

    from app.main import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    tmp_dir = tempfile.mkdtemp()
    original_upload_dir = settings.upload_dir
    settings.upload_dir = Path(tmp_dir)

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
    settings.upload_dir = original_upload_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# PDF fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_pdf_path() -> Path:
    """Path to the simple_table.pdf test fixture."""
    return FIXTURES_DIR / "simple_table.pdf"


@pytest.fixture()
def sample_pdf_bytes(sample_pdf_path: Path) -> bytes:
    """Raw bytes of the simple_table.pdf test fixture."""
    return sample_pdf_path.read_bytes()


@pytest.fixture()
def not_a_pdf() -> bytes:
    """Bytes that are not a valid PDF."""
    return b"This is not a PDF file at all."
