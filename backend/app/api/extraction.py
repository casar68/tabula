"""Table extraction endpoints."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.schemas.extraction import ExtractionRequest, ExtractionResponse, TableResult
from app.services import export_service, extraction_service
from app.services.storage_service import get_document_path

router = APIRouter(prefix="/documents", tags=["extraction"])


@router.post("/{document_id}/extract", response_model=ExtractionResponse)
def extract_tables(
    document_id: UUID,
    request: ExtractionRequest,
    db: Session = Depends(get_db),
):
    """Extract tables from selected regions of a PDF."""
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

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
):
    """Extract tables and download in the specified format."""
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

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
            "Content-Disposition": f'attachment; filename="{download_name}"',
        },
    )
