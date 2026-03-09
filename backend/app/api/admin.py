"""Admin API endpoints -- user management, settings, and mode switching."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import (
    AppConfig,
    ensure_secret_key,
    get_app_config,
    save_app_config,
    settings,
)
from app.core.auth import hash_password
from app.core.dependencies import require_admin
from app.database import get_db, reset_engine
from app.models.user import User
from app.schemas.admin import SwitchModeResponse, SwitchToMonoRequest, SwitchToMultiRequest
from app.schemas.auth import RegisterRequest, UserListResponse, UserResponse
from app.services.db_init_service import (
    init_postgres_database,
    init_sqlite_database,
    test_database_connection,
)
from app.services.migration_service import migrate_postgres_to_sqlite, migrate_sqlite_to_postgres

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@router.get("/users", response_model=UserListResponse)
def list_users(
    db: Session = Depends(get_db),
    _admin: User | None = Depends(require_admin),
):
    """List all users (admin only)."""
    users = db.query(User).order_by(User.created_at).all()
    return UserListResponse(users=users, total=len(users))


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    req: RegisterRequest,
    db: Session = Depends(get_db),
    _admin: User | None = Depends(require_admin),
):
    """Create a new user (admin only)."""
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("Admin created user: %s", user.username)
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User | None = Depends(require_admin),
):
    """Delete a user (admin only). Cannot delete yourself."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if admin is not None and user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    db.delete(user)
    db.commit()
    logger.info("Admin deleted user: %s", user.username)


# ---------------------------------------------------------------------------
# App settings
# ---------------------------------------------------------------------------

@router.put("/settings")
def update_settings(
    allow_registration: bool | None = None,
    _admin: User | None = Depends(require_admin),
):
    """Update application settings (admin only)."""
    cfg = get_app_config()
    changed = False

    if allow_registration is not None and cfg.allow_registration != allow_registration:
        cfg.allow_registration = allow_registration
        changed = True

    if changed:
        save_app_config(cfg)

    return {"allow_registration": cfg.allow_registration}


# ---------------------------------------------------------------------------
# Mode switching
# ---------------------------------------------------------------------------

@router.post("/switch-to-multi", response_model=SwitchModeResponse)
def switch_to_multi(
    req: SwitchToMultiRequest,
    _admin: User | None = Depends(require_admin),
):
    """Switch from mono to multi-user mode."""
    cfg = get_app_config()
    if cfg.mode == "multi":
        raise HTTPException(status_code=400, detail="Already in multi-user mode")

    pg_url = (
        f"postgresql://{req.pg_user}:{req.pg_password}"
        f"@{req.pg_host}:{req.pg_port}/{req.pg_database}"
    )

    # Test connection
    ok, msg = test_database_connection(pg_url)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Cannot connect to PostgreSQL: {msg}")

    # Create tables in PG
    init_postgres_database(pg_url)

    # Save new config & reset engine to use PG
    old_db_url = cfg.database_url
    new_config = AppConfig(
        mode="multi",
        database_url=pg_url,
        setup_completed=True,
        allow_registration=cfg.allow_registration,
        secret_key=cfg.secret_key,
    )
    new_config = ensure_secret_key(new_config)
    save_app_config(new_config)
    reset_engine()

    # Create admin user in the new PG database
    from app.database import get_session_factory

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
        session.refresh(admin)
        admin_id = admin.id
    finally:
        session.close()

    # Optionally migrate data from SQLite
    migrated = None
    if req.migrate_data and old_db_url.startswith("sqlite"):
        sqlite_path = old_db_url.replace("sqlite:///", "")
        migrated = migrate_sqlite_to_postgres(sqlite_path, pg_url, admin_id)

    logger.info("Switched to MULTI mode, admin '%s' created", req.admin_username)
    return SwitchModeResponse(
        success=True,
        mode="multi",
        message=f"Switched to multi-user mode, admin '{req.admin_username}' created",
        migrated=migrated,
    )


@router.post("/switch-to-mono", response_model=SwitchModeResponse)
def switch_to_mono(
    req: SwitchToMonoRequest,
    _admin: User | None = Depends(require_admin),
):
    """Switch from multi to mono-user mode."""
    cfg = get_app_config()
    if cfg.mode == "mono":
        raise HTTPException(status_code=400, detail="Already in mono mode")

    old_pg_url = cfg.database_url
    sqlite_path = str(settings.data_dir / "tabula.db")
    sqlite_url = f"sqlite:///{sqlite_path}"

    # Create fresh SQLite database
    init_sqlite_database(sqlite_path)

    # Migrate selected data
    migrated = migrate_postgres_to_sqlite(
        pg_url=old_pg_url,
        sqlite_path=sqlite_path,
        source_user_id=req.source_user_id,
        include_all=req.include_all_users,
    )

    # Update config
    new_config = AppConfig(
        mode="mono",
        database_url=sqlite_url,
        setup_completed=True,
        allow_registration=cfg.allow_registration,
        secret_key=cfg.secret_key,
    )
    save_app_config(new_config)
    reset_engine()

    logger.info("Switched to MONO mode")
    return SwitchModeResponse(
        success=True,
        mode="mono",
        message="Switched to mono-user mode",
        migrated=migrated,
    )
