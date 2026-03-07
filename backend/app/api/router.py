"""Aggregates all API routers."""

from fastapi import APIRouter

from app.api import documents, extraction, jobs, templates

api_router = APIRouter(prefix="/api")

api_router.include_router(documents.router)
api_router.include_router(extraction.router)
api_router.include_router(templates.router)
api_router.include_router(jobs.router)
