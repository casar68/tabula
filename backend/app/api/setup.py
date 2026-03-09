"""Setup wizard API -- first-run configuration."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.config import (
    AppConfig,
    ensure_secret_key,
    get_app_config,
    save_app_config,
    settings,
)
from app.core.rate_limit import limiter
from app.database import reset_engine
from app.schemas.setup import SetupRequest, SetupResponse, SetupStatusResponse
from app.services.db_init_service import (
    init_postgres_database,
    init_sqlite_database,
    test_database_connection,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/setup", tags=["setup"])


@router.get("/status", response_model=SetupStatusResponse)
def get_setup_status():
    """Check whether the initial setup has been completed."""
    cfg = get_app_config()
    return SetupStatusResponse(
        setup_completed=cfg.setup_completed,
        mode=cfg.mode if cfg.setup_completed else None,
    )


@router.post("/init", response_model=SetupResponse)
@limiter.limit("3/minute")
def init_setup(request: Request, req: SetupRequest):
    """Initialise the application in mono or multi mode."""
    cfg = get_app_config()
    if cfg.setup_completed:
        raise HTTPException(status_code=400, detail="Setup already completed")

    if req.mode == "mono":
        return _init_mono()
    else:
        return _init_multi(req)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _init_mono() -> SetupResponse:
    db_path = str(settings.data_dir / "tabula.db")
    db_url = f"sqlite:///{db_path}"

    init_sqlite_database(db_path)

    config = AppConfig(
        mode="mono",
        database_url=db_url,
        setup_completed=True,
    )
    config = ensure_secret_key(config)
    save_app_config(config)
    reset_engine()

    logger.info("Setup completed in MONO mode")
    return SetupResponse(success=True, mode="mono", message="Mono-user mode initialised")


def _init_multi(req: SetupRequest) -> SetupResponse:
    # Validate required fields
    for field in ("pg_host", "pg_user", "pg_password", "pg_database",
                  "admin_username", "admin_password"):
        if not getattr(req, field, None):
            raise HTTPException(
                status_code=422,
                detail=f"Field '{field}' is required for multi-user setup",
            )

    pg_url = (
        f"postgresql://{req.pg_user}:{req.pg_password}"
        f"@{req.pg_host}:{req.pg_port}/{req.pg_database}"
    )

    # Test PostgreSQL connectivity
    ok, msg = test_database_connection(pg_url)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Cannot connect to PostgreSQL: {msg}")

    # Create tables
    init_postgres_database(pg_url)

    # Create admin user (imported lazily to avoid circular imports at module level)
    from app.core.auth import hash_password
    from app.database import get_session_factory
    from app.models.user import User

    config = AppConfig(
        mode="multi",
        database_url=pg_url,
        setup_completed=True,
        allow_registration=True,
    )
    config = ensure_secret_key(config)
    save_app_config(config)
    reset_engine()

    # Now create the admin in the newly configured database
    factory = get_session_factory()
    session = factory()
    try:
        admin = User(
            username=req.admin_username,
            password_hash=hash_password(req.admin_password),
            is_admin=True,
        )
        session.add(admin)
        session.commit()
    finally:
        session.close()

    logger.info("Setup completed in MULTI mode, admin '%s' created", req.admin_username)
    return SetupResponse(
        success=True,
        mode="multi",
        message=f"Multi-user mode initialised, admin '{req.admin_username}' created",
    )
