"""Table extraction from PDFs using pdfplumber."""

from pathlib import Path

import pdfplumber

from app.schemas.extraction import ExtractionSelection


def _get_table_settings(method: str, cropped_page) -> dict:
    """Map extraction method to pdfplumber table_settings."""
    if method == "guess":
        # Auto-detect: use lattice if lines are present, otherwise stream
        has_lines = len(cropped_page.lines) > 0 if hasattr(cropped_page, "lines") else False
        if has_lines:
            method = "lattice"
        else:
            method = "stream"

    if method == "lattice":
        return {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
        }
    else:  # stream
        return {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
        }


def extract_tables(
    pdf_path: Path,
    selections: list[ExtractionSelection],
) -> list[dict]:
    """Extract tables from specified regions of a PDF.

    Returns a list of dicts, each with spec_index, page, and data (2D array of strings).
    """
    results = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, sel in enumerate(selections):
            page_index = sel.page - 1  # pdfplumber is 0-indexed
            if page_index < 0 or page_index >= len(pdf.pages):
                results.append({
                    "spec_index": i,
                    "page": sel.page,
                    "data": [],
                })
                continue

            page = pdf.pages[page_index]

            # Crop to the selected region
            # pdfplumber uses (x0, top, x1, bottom) with top-left origin
            bbox = (sel.x1, sel.y1, sel.x2, sel.y2)

            try:
                cropped = page.crop(bbox)
            except Exception:
                # If crop fails (e.g., bbox out of bounds), return empty
                results.append({
                    "spec_index": i,
                    "page": sel.page,
                    "data": [],
                })
                continue

            settings = _get_table_settings(sel.extraction_method, cropped)

            try:
                tables = cropped.extract_tables(settings)
            except Exception:
                tables = []

            # Flatten multiple tables into one result per selection
            all_rows: list[list[str]] = []
            for table in tables:
                for row in table:
                    # Replace None cells with empty strings
                    all_rows.append([cell or "" for cell in row])

            results.append({
                "spec_index": i,
                "page": sel.page,
                "data": all_rows,
            })

    return results


def detect_tables(pdf_path: Path) -> list[dict]:
    """Auto-detect table regions in all pages of a PDF.

    Returns a list of detected table bounding boxes.
    """
    detected = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            page_number = page.page_number  # 1-indexed in pdfplumber
            try:
                tables = page.find_tables()
            except Exception:
                continue

            for table in tables:
                bbox = table.bbox  # (x0, top, x1, bottom)
                detected.append({
                    "page": page_number,
                    "x1": round(bbox[0], 2),
                    "y1": round(bbox[1], 2),
                    "x2": round(bbox[2], 2),
                    "y2": round(bbox[3], 2),
                    "width": round(bbox[2] - bbox[0], 2),
                    "height": round(bbox[3] - bbox[1], 2),
                })

    return detected
