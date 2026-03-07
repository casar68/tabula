"""Background job management for PDF processing."""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.job import Job
from app.services import extraction_service, pdf_service
from app.services.storage_service import get_document_path

logger = logging.getLogger(__name__)


def process_document(db: Session, document_id: UUID, job_id: UUID) -> None:
    """Background task: analyze a PDF document.

    1. Extract metadata (page count, dimensions)
    2. Validate text content
    3. Auto-detect tables
    4. Update document and job records
    """
    job = db.get(Job, job_id)
    if not job:
        return

    try:
        job.status = "working"
        job.progress = 5
        job.message = "Extracting PDF metadata..."
        db.commit()

        pdf_path = get_document_path(document_id)

        # Step 1: Extract metadata with PyMuPDF
        metadata = pdf_service.extract_pdf_metadata(pdf_path)
        job.progress = 20
        job.message = "Checking text content..."
        db.commit()

        # Step 2: Validate text content
        has_text = pdf_service.validate_pdf_has_text(pdf_path)
        if not has_text:
            job.status = "failed"
            job.error_type = "no-text"
            job.message = "This PDF does not contain extractable text."
            db.commit()
            return

        # Step 3: Update document with metadata
        from app.models.document import Document

        document = db.get(Document, document_id)
        if document:
            document.page_count = metadata["page_count"]
            document.pages = metadata["pages"]

        job.progress = 50
        job.message = "Detecting tables..."
        db.commit()

        # Step 4: Auto-detect tables
        try:
            detected_tables = extraction_service.detect_tables(pdf_path)
            if document:
                document.detected_tables = detected_tables
        except Exception as e:
            logger.warning("Table detection failed for %s: %s", document_id, e)
            # Non-fatal: continue even if detection fails

        job.progress = 100
        job.status = "completed"
        job.message = "Processing complete."
        db.commit()

    except Exception as e:
        logger.exception("Job %s failed: %s", job_id, e)
        job.status = "failed"
        job.error_type = "unknown"
        job.message = str(e)
        db.commit()
