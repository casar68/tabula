"""Aggregates all API routers."""

from fastapi import APIRouter

from app.api import admin, auth, documents, extraction, jobs, setup, templates

api_router = APIRouter(prefix="/api")

api_router.include_router(setup.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(documents.router)
api_router.include_router(extraction.router)
api_router.include_router(templates.router)
api_router.include_router(jobs.router)
