"""Tabula -- PDF Table Extraction Tool."""

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.config import get_app_config, is_setup_completed, settings
from app.core.rate_limit import limiter
from app.core.worker_pool import shutdown_executor

# Configure structured logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    yield
    # Shutdown: wait for background processing threads to finish
    logger.info("Shutting down worker pool...")
    shutdown_executor()
    logger.info("Worker pool shut down.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Extract tables from PDF files",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Setup gate middleware -- block API access until setup is completed
SETUP_EXEMPT_PREFIXES = ("/api/setup", "/api/settings")


@app.middleware("http")
async def setup_gate(request: Request, call_next):
    """Return 503 on all /api/* routes (except setup & settings) if setup is pending."""
    path = request.url.path
    if path.startswith("/api/") and not any(path.startswith(p) for p in SETUP_EXEMPT_PREFIXES):
        if not is_setup_completed():
            return JSONResponse(
                status_code=503,
                content={"detail": "Setup required", "setup_required": True},
            )
    return await call_next(request)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %d (%.0f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


# Global exception handler
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# CORS (for Vite dev server on a different port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(api_router)


@app.get("/api/settings")
def get_settings():
    """Return application settings for the frontend."""
    cfg = get_app_config()
    return {
        "app_version": settings.app_version,
        "app_name": settings.app_name,
        "setup_completed": cfg.setup_completed,
        "mode": cfg.mode,
        "allow_registration": cfg.allow_registration,
    }


# Serve built frontend in production (if static/ directory exists)
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the React SPA for all non-API routes."""
        # Try to serve the exact file first
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html (SPA routing)
        return FileResponse(str(STATIC_DIR / "index.html"))
