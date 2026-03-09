"""Document management endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.job_manager import process_document
from app.core.rate_limit import limiter
from app.core.worker_pool import get_executor
from app.database import get_db
from app.models.document import Document
from app.models.job import Job
from app.models.user import User
from app.schemas.document import (
    DetectedTablesResponse,
    DocumentListResponse,
    DocumentResponse,
    UploadBatchResponse,
    UploadResponse,
)
from app.services.storage_service import (
    compute_sha256,
    delete_document_files,
    get_document_path,
    save_uploaded_file,
    validate_pdf,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Maximum upload size: 100 MB
MAX_UPLOAD_SIZE = 100 * 1024 * 1024


def _check_document_access(doc: Document | None, user: User | None) -> Document:
    """Verify document exists and the user has access to it.

    In mono mode (user is None) all documents are accessible.
    In multi mode, admins see everything; regular users only their own docs.
    """
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if user is not None and not user.is_admin and doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/upload", response_model=UploadBatchResponse)
@limiter.limit("20/minute")
async def upload_documents(
    request: Request,
    files: list[UploadFile],
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Upload one or more PDF files for processing."""
    uploads = []
    pending_jobs: list[tuple[UUID, UUID]] = []

    for file in files:
        content = await file.read()

        # Check file size
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"'{file.filename}' exceeds the"
                    f" {MAX_UPLOAD_SIZE // (1024 * 1024)} MB limit."
                ),
            )

        # Validate PDF magic bytes
        if not validate_pdf(content):
            raise HTTPException(
                status_code=400,
                detail=f"'{file.filename}' is not a valid PDF file.",
            )

        # Create document record
        doc = Document(
            original_filename=file.filename or "document.pdf",
            file_path="",  # Will be set after saving
            file_size=len(content),
            sha256=compute_sha256(content),
            user_id=user.id if user else None,
        )
        db.add(doc)
        db.flush()  # Get the ID

        # Save file to disk
        file_path = save_uploaded_file(doc.id, content, doc.original_filename)
        doc.file_path = str(file_path)

        # Create processing job
        job = Job(document_id=doc.id)
        db.add(job)
        db.flush()

        uploads.append(UploadResponse(
            id=doc.id,
            job_id=job.id,
            original_filename=doc.original_filename,
        ))

        pending_jobs.append((doc.id, job.id))

    # Commit first so background threads can read the records
    db.commit()

    # Launch background processing threads after commit
    from app.database import SessionLocal

    for doc_id, job_id in pending_jobs:

        def _run_job(d_id: UUID = doc_id, j_id: UUID = job_id) -> None:
            session = SessionLocal()
            try:
                process_document(session, d_id, j_id)
            except Exception:
                logger.exception("Background job %s failed", j_id)
            finally:
                session.close()

        get_executor().submit(_run_job)

    return UploadBatchResponse(uploads=uploads)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """List uploaded documents with pagination (filtered by user in multi mode)."""
    query = db.query(Document)
    count_query = db.query(sa_func.count(Document.id))

    # In multi mode, non-admins see only their own documents
    if user is not None and not user.is_admin:
        query = query.filter(Document.user_id == user.id)
        count_query = count_query.filter(Document.user_id == user.id)

    total = count_query.scalar() or 0
    docs = (
        query.order_by(Document.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Get metadata for a specific document."""
    doc = _check_document_access(db.get(Document, document_id), user)
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}")
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Delete a document and its associated files."""
    doc = _check_document_access(db.get(Document, document_id), user)

    delete_document_files(document_id)
    db.delete(doc)
    db.commit()
    return {"detail": "Document deleted"}


@router.get("/{document_id}/file")
def serve_pdf(
    document_id: UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Serve the PDF file for client-side rendering with react-pdf."""
    doc = _check_document_access(db.get(Document, document_id), user)

    pdf_path = get_document_path(document_id)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=doc.original_filename,
    )


@router.get("/{document_id}/tables", response_model=DetectedTablesResponse)
def get_detected_tables(
    document_id: UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Get auto-detected table regions for a document."""
    doc = _check_document_access(db.get(Document, document_id), user)

    tables = doc.detected_tables or []
    return DetectedTablesResponse(tables=tables)
