"""Table extraction from PDFs using PyMuPDF with OCR fallback.

Uses PyMuPDF (fitz) for table structure detection and text extraction.
When the PDF uses custom font encodings that produce garbled text,
automatically falls back to OCR via Tesseract (pytesseract) with
sparse-text mode (--psm 11) and coverage-based column detection.
"""

import io
import logging
import re
from pathlib import Path

import fitz  # PyMuPDF

from app.schemas.extraction import ExtractionSelection

logger = logging.getLogger(__name__)

# Try to import pytesseract for OCR fallback
try:
    import pytesseract
    from PIL import Image

    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    logger.info("pytesseract/Pillow not installed — OCR fallback disabled")


# ---------------------------------------------------------------------------
# Garbled-text detection
# ---------------------------------------------------------------------------

_NORMAL_CHARS = re.compile(
    r"[a-zA-ZÀ-ÿ0-9.,;:!?'\"()\-/%€$£@#&+=°\[\]{}*]"
)


def _is_garbled(text: str, threshold: float = 0.4) -> bool:
    """Heuristic: detect garbled text from bad font encodings.

    Checks the ratio of "normal" characters (letters incl. accented,
    digits, common punctuation) to total non-whitespace characters.
    """
    cleaned = re.sub(r"\s+", "", text)
    if len(cleaned) < 10:
        return False
    ratio = len(_NORMAL_CHARS.findall(cleaned)) / len(cleaned)
    return ratio < threshold


# ---------------------------------------------------------------------------
# OCR-based table extraction (sparse text + y-clustering rows)
# ---------------------------------------------------------------------------

def _ocr_region_to_table(
    page: fitz.Page,
    clip: fitz.Rect,
    lang: str = "fra+eng",
    dpi: int = 300,
) -> list[list[str]]:
    """OCR a region and reconstruct table structure.

    Uses Tesseract's sparse text mode (--psm 11) which finds words
    independently without imposing reading order — critical for tables
    with grid lines that confuse Tesseract's layout analysis.

    Pipeline:
      1. Render the clipped region at high DPI.
      2. Run Tesseract --psm 11 to get individual word positions.
      3. Cluster words into rows by y-position proximity.
      4. Detect columns via PDF header structure or coverage gaps.
      5. Map each word to its column and build the table.
    """
    if not HAS_OCR:
        return []

    scale = dpi / 72
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, clip=clip)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    img_w = img.size[0]

    # --- Word-level OCR with sparse text mode -----------------------------
    # --psm 11 = sparse text: finds words without assuming reading order.
    # This avoids row/column confusion caused by table grid lines.
    ocr = pytesseract.image_to_data(
        img, lang=lang, config="--psm 11",
        output_type=pytesseract.Output.DICT,
    )

    words: list[dict] = []
    for i in range(len(ocr["text"])):
        text = str(ocr["text"][i]).strip()
        conf = int(ocr["conf"][i])
        if text and conf > 0:
            words.append({
                "text": text,
                "left": ocr["left"][i],
                "top": ocr["top"][i],
                "width": ocr["width"][i],
                "height": ocr["height"][i],
            })

    if not words:
        return []

    # --- Cluster words into rows by y-position ----------------------------
    rows = _cluster_words_into_rows(words)

    # --- Detect column boundaries -----------------------------------------
    col_bounds = _detect_columns_from_coverage(rows, img_w)

    n_cols = len(col_bounds) - 1
    if n_cols < 1:
        return [
            [" ".join(w["text"] for w in sorted(rw, key=lambda w: w["left"]))]
            for rw in rows
        ]

    # --- Map words to columns and build table -----------------------------
    table: list[list[str]] = []
    for row_words in rows:
        cells = [""] * n_cols
        for w in sorted(row_words, key=lambda w: w["left"]):
            center_x = w["left"] + w["width"] / 2
            col = 0
            for j in range(n_cols):
                if center_x >= col_bounds[j]:
                    col = j
            if col < n_cols:
                prev = cells[col]
                cells[col] = f"{prev} {w['text']}".strip() if prev else w["text"]
        if any(c.strip() for c in cells):
            table.append(cells)

    return table


def _cluster_words_into_rows(
    words: list[dict],
    tolerance_ratio: float = 0.5,
) -> list[list[dict]]:
    """Cluster words into rows based on vertical center proximity.

    Two words belong to the same row if their vertical centers are
    within ``tolerance_ratio * median_word_height`` pixels of each other.

    Returns rows sorted top-to-bottom.
    """
    if not words:
        return []

    heights = sorted(w["height"] for w in words)
    median_h = heights[len(heights) // 2]
    tolerance = max(5, int(median_h * tolerance_ratio))

    sorted_words = sorted(words, key=lambda w: w["top"] + w["height"] / 2)

    rows: list[list[dict]] = []
    current_row: list[dict] = [sorted_words[0]]
    current_y = sorted_words[0]["top"] + sorted_words[0]["height"] / 2

    for w in sorted_words[1:]:
        w_center_y = w["top"] + w["height"] / 2
        if abs(w_center_y - current_y) <= tolerance:
            current_row.append(w)
            current_y = sum(
                ww["top"] + ww["height"] / 2 for ww in current_row
            ) / len(current_row)
        else:
            rows.append(current_row)
            current_row = [w]
            current_y = w_center_y

    if current_row:
        rows.append(current_row)

    return rows


# ---------------------------------------------------------------------------
# Column detection: coverage-based
# ---------------------------------------------------------------------------

def _detect_columns_from_coverage(
    rows: list[list[dict]],
    img_width: int,
) -> list[int]:
    """Detect column boundaries by finding vertical text-free gaps.

    Uses an adaptive minimum gap width based on image size to avoid
    detecting too many false columns from digit separators or sparse
    sections.
    """
    n_rows = len(rows)
    if n_rows == 0 or img_width <= 0:
        return [0, img_width]

    # Adaptive min gap: ~3% of image width (e.g., 70px for 2300px image)
    min_gap_px = max(40, img_width // 30)

    coverage = [0] * img_width

    for row_words in rows:
        filled: set[int] = set()
        for w in row_words:
            x_start = max(0, w["left"])
            x_end = min(w["left"] + w["width"], img_width)
            filled.update(range(x_start, x_end))
        for x in filled:
            coverage[x] += 1

    # Gap = x-ranges where coverage < 15% of rows
    threshold = max(2, int(n_rows * 0.15))

    gap_regions: list[tuple[int, int]] = []
    in_gap = False
    gap_start = 0
    for x in range(img_width):
        if coverage[x] < threshold:
            if not in_gap:
                gap_start = x
                in_gap = True
        else:
            if in_gap:
                gap_regions.append((gap_start, x))
                in_gap = False
    if in_gap:
        gap_regions.append((gap_start, img_width))

    # Keep significant interior gaps (exclude edge-touching, wide enough)
    significant = []
    for g_start, g_end in gap_regions:
        width = g_end - g_start
        if width < min_gap_px:
            continue
        # Exclude gaps that touch the right edge (often sparse tail areas)
        if g_end >= img_width - 10 and width > img_width * 0.1:
            continue
        significant.append((g_start, g_end, width))

    # Sort by width descending and keep the most prominent gaps
    significant.sort(key=lambda g: -g[2])

    # Use natural-break detection: if there's a big drop in gap width,
    # only keep the wider gaps (likely real column separators)
    if len(significant) > 1:
        widths = [g[2] for g in significant]
        cutoff_idx = len(widths)
        for i in range(1, len(widths)):
            ratio = widths[i] / widths[i - 1]
            if ratio < 0.65 and i >= 3:
                cutoff_idx = i
                break
        significant = significant[:cutoff_idx]

    # Sort back by position
    significant.sort(key=lambda g: g[0])

    # Build boundaries from gap midpoints
    bounds = [0]
    for g_start, g_end, _ in significant:
        mid = (g_start + g_end) // 2
        if mid > bounds[-1] + 30:
            bounds.append(mid)
    if bounds[-1] < img_width - 30:
        bounds.append(img_width)

    return bounds


# ---------------------------------------------------------------------------
# Strategy detection
# ---------------------------------------------------------------------------

def _get_strategy(method: str, page: fitz.Page, clip: fitz.Rect) -> str:
    """Resolve extraction method to PyMuPDF strategy ('lines' or 'text')."""
    if method == "lattice":
        return "lines"
    if method == "stream":
        return "text"

    # Auto-detect: count line drawings inside the clip
    drawings = page.get_drawings()
    line_count = 0
    for d in drawings:
        for item in d.get("items", []):
            kind = item[0]
            if kind == "l":
                p1, p2 = fitz.Point(item[1]), fitz.Point(item[2])
                if clip.contains(p1) or clip.contains(p2):
                    line_count += 1
            elif kind == "re":
                rect = fitz.Rect(item[1])
                if clip.intersects(rect):
                    line_count += 4
    return "lines" if line_count >= 4 else "text"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_tables(
    pdf_path: Path,
    selections: list[ExtractionSelection],
) -> list[dict]:
    """Extract tables from specified regions of a PDF.

    Pipeline:
      1. Use ``page.find_tables()`` for structure + text.
      2. If the extracted text looks garbled (custom font encoding),
         fall back to full-region OCR with column detection.

    Returns a list of dicts with *spec_index*, *page*, and *data*.
    """
    results: list[dict] = []

    doc = fitz.open(str(pdf_path))
    try:
        for i, sel in enumerate(selections):
            page_index = sel.page - 1
            if page_index < 0 or page_index >= len(doc):
                results.append({"spec_index": i, "page": sel.page, "data": []})
                continue

            page = doc[page_index]
            clip = fitz.Rect(sel.x1, sel.y1, sel.x2, sel.y2)
            strategy = _get_strategy(sel.extraction_method, page, clip)

            try:
                tabs = page.find_tables(clip=clip, strategy=strategy)
            except Exception:
                tabs = None

            # --- First pass: normal text extraction -----------------------
            combined_text = ""
            normal_data: list[list[list[str]]] = []
            if tabs and tabs.tables:
                for table in tabs.tables:
                    try:
                        data = table.extract()
                        normal_data.append(data)
                        for row in data:
                            combined_text += " ".join(
                                cell for cell in row if cell
                            )
                    except Exception:
                        normal_data.append([])

            # --- Decide: normal path or OCR fallback ----------------------
            use_ocr = _is_garbled(combined_text) and HAS_OCR
            all_rows: list[list[str]] = []

            if use_ocr:
                logger.info(
                    "Garbled text on page %d — falling back to OCR",
                    sel.page,
                )
                all_rows = _ocr_region_to_table(page, clip)
            elif normal_data:
                for table_data in normal_data:
                    for row in table_data:
                        all_rows.append(
                            [cell if cell is not None else "" for cell in row]
                        )
            elif HAS_OCR:
                # No tables found at all — try OCR as last resort
                all_rows = _ocr_region_to_table(page, clip)

            results.append({
                "spec_index": i,
                "page": sel.page,
                "data": all_rows,
            })
    finally:
        doc.close()

    return results


def detect_tables(pdf_path: Path) -> list[dict]:
    """Auto-detect table regions in all pages of a PDF.

    Returns bounding-box dicts (page, x1, y1, x2, y2, width, height).
    """
    detected: list[dict] = []

    doc = fitz.open(str(pdf_path))
    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            page_number = page_index + 1

            try:
                tabs = page.find_tables()
            except Exception:
                continue

            for table in tabs.tables:
                bbox = table.bbox
                detected.append({
                    "page": page_number,
                    "x1": round(bbox[0], 2),
                    "y1": round(bbox[1], 2),
                    "x2": round(bbox[2], 2),
                    "y2": round(bbox[3], 2),
                    "width": round(bbox[2] - bbox[0], 2),
                    "height": round(bbox[3] - bbox[1], 2),
                })
    finally:
        doc.close()

    return detected
