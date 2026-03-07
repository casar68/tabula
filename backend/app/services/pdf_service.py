"""PDF metadata extraction using PyMuPDF (fitz)."""

from pathlib import Path

import fitz  # PyMuPDF


def extract_pdf_metadata(pdf_path: Path) -> dict:
    """Extract page metadata from a PDF file.

    Returns a dict with page_count and pages (list of page info dicts).
    """
    doc = fitz.open(str(pdf_path))
    try:
        pages = []
        for i, page in enumerate(doc):
            rect = page.rect
            pages.append({
                "number": i + 1,
                "width": round(rect.width, 2),
                "height": round(rect.height, 2),
                "rotation": page.rotation,
            })

        return {
            "page_count": len(pages),
            "pages": pages,
        }
    finally:
        doc.close()


def validate_pdf_has_text(pdf_path: Path) -> bool:
    """Check if the PDF contains extractable text on at least one page."""
    doc = fitz.open(str(pdf_path))
    try:
        for page in doc:
            text = page.get_text().strip()
            if text:
                return True
        return False
    finally:
        doc.close()
