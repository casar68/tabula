"""Document management endpoints."""

import threading
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.job_manager import process_document
from app.database import get_db
from app.models.document import Document
from app.models.job import Job
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

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadBatchResponse)
async def upload_documents(
    files: list[UploadFile],
    db: Session = Depends(get_db),
):
    """Upload one or more PDF files for processing."""
    uploads = []

    for file in files:
        content = await file.read()

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

        # Launch background processing in a thread
        # (FastAPI BackgroundTasks runs after response, but we need a fresh session)
        from app.database import SessionLocal

        def _run_job(doc_id=doc.id, j_id=job.id):
            session = SessionLocal()
            try:
                process_document(session, doc_id, j_id)
            finally:
                session.close()

        thread = threading.Thread(target=_run_job, daemon=True)
        thread.start()

    db.commit()
    return UploadBatchResponse(uploads=uploads)


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return DocumentListResponse(documents=[DocumentResponse.model_validate(d) for d in docs])


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    """Get metadata for a specific document."""
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}")
def delete_document(document_id: UUID, db: Session = Depends(get_db)):
    """Delete a document and its associated files."""
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_files(document_id)
    db.delete(doc)
    db.commit()
    return {"detail": "Document deleted"}


@router.get("/{document_id}/file")
def serve_pdf(document_id: UUID, db: Session = Depends(get_db)):
    """Serve the PDF file for client-side rendering with react-pdf."""
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pdf_path = get_document_path(document_id)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=doc.original_filename,
    )


@router.get("/{document_id}/tables", response_model=DetectedTablesResponse)
def get_detected_tables(document_id: UUID, db: Session = Depends(get_db)):
    """Get auto-detected table regions for a document."""
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    tables = doc.detected_tables or []
    return DetectedTablesResponse(tables=tables)
