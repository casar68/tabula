import hashlib
import shutil
from pathlib import Path
from uuid import UUID

from app.config import settings


def get_document_dir(document_id: UUID) -> Path:
    """Return the storage directory for a document."""
    doc_dir = settings.upload_dir / str(document_id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    return doc_dir


def save_uploaded_file(document_id: UUID, file_content: bytes, filename: str) -> Path:
    """Save an uploaded PDF file to disk. Returns the file path."""
    doc_dir = get_document_dir(document_id)
    file_path = doc_dir / "document.pdf"
    file_path.write_bytes(file_content)
    return file_path


def get_document_path(document_id: UUID) -> Path:
    """Return the path to a document's PDF file."""
    return get_document_dir(document_id) / "document.pdf"


def delete_document_files(document_id: UUID) -> None:
    """Delete all files associated with a document."""
    doc_dir = settings.upload_dir / str(document_id)
    if doc_dir.exists():
        shutil.rmtree(doc_dir)


def compute_sha256(content: bytes) -> str:
    """Compute SHA256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def validate_pdf(content: bytes) -> bool:
    """Check if the content starts with the PDF magic bytes."""
    return content[:5] == b"%PDF-"
