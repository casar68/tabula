"""Table extraction endpoints."""

from pathlib import Path
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.extraction import ExtractionRequest, ExtractionResponse, TableResult
from app.services import export_service, extraction_service
from app.services.storage_service import get_document_path


def _safe_content_disposition(filename: str) -> str:
    """Build a safe Content-Disposition header value (RFC 5987)."""
    # ASCII fallback: strip non-ASCII and dangerous characters
    ascii_name = filename.encode("ascii", "ignore").decode("ascii")
    ascii_name = ascii_name.replace('"', "").replace("\r", "").replace("\n", "")
    # UTF-8 encoded version for modern browsers
    encoded = quote(filename, safe="")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}"


def _check_doc(db: Session, document_id: UUID, user: User | None) -> Document:
    """Verify document exists and the user has access."""
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if user is not None and not user.is_admin and doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


router = APIRouter(prefix="/documents", tags=["extraction"])


@router.post("/{document_id}/extract", response_model=ExtractionResponse)
def extract_tables(
    document_id: UUID,
    request: ExtractionRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Extract tables from selected regions of a PDF."""
    _check_doc(db, document_id, user)

    pdf_path = get_document_path(document_id)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    raw_tables = extraction_service.extract_tables(pdf_path, request.selections)

    tables = [
        TableResult(spec_index=t["spec_index"], page=t["page"], data=t["data"])
        for t in raw_tables
    ]

    return ExtractionResponse(tables=tables)


@router.post("/{document_id}/export")
def export_tables(
    document_id: UUID,
    request: ExtractionRequest,
    format: str = Query(default="csv", pattern="^(csv|tsv|json|zip)$"),
    filename: str = Query(default=None),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Extract tables and download in the specified format."""
    doc = _check_doc(db, document_id, user)

    pdf_path = get_document_path(document_id)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    raw_tables = extraction_service.extract_tables(pdf_path, request.selections)

    exporter = export_service.EXPORTERS.get(format)
    if not exporter:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    base_name = filename or Path(doc.original_filename).stem
    download_name = f"{base_name}{exporter['extension']}"

    if format == "zip":
        content = exporter["fn"](raw_tables, base_name)
    else:
        content = exporter["fn"](raw_tables)
        content = content.encode("utf-8")

    return Response(
        content=content,
        media_type=exporter["content_type"],
        headers={
            "Content-Disposition": _safe_content_disposition(download_name),
        },
    )
