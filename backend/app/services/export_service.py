"""Export extracted table data to various formats."""

import csv
import io
import json
import zipfile


def to_csv(tables: list[dict]) -> str:
    """Convert extracted tables to a single CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    for table in tables:
        for row in table["data"]:
            writer.writerow(row)
        # Empty row between tables
        if len(tables) > 1:
            writer.writerow([])
    return output.getvalue()


def to_tsv(tables: list[dict]) -> str:
    """Convert extracted tables to a single TSV string."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t")
    for table in tables:
        for row in table["data"]:
            writer.writerow(row)
        if len(tables) > 1:
            writer.writerow([])
    return output.getvalue()


def to_json(tables: list[dict]) -> str:
    """Convert extracted tables to a JSON string."""
    return json.dumps(tables, ensure_ascii=False, indent=2)


def to_zip(tables: list[dict], base_filename: str = "tabula") -> bytes:
    """Convert extracted tables to a ZIP archive with one CSV per table."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, table in enumerate(tables):
            csv_output = io.StringIO()
            writer = csv.writer(csv_output)
            for row in table["data"]:
                writer.writerow(row)
            filename = f"{base_filename}-page{table['page']}-table{i + 1}.csv"
            zf.writestr(filename, csv_output.getvalue())
    return buffer.getvalue()


EXPORTERS = {
    "csv": {"fn": to_csv, "content_type": "text/csv", "extension": ".csv"},
    "tsv": {"fn": to_tsv, "content_type": "text/tab-separated-values", "extension": ".tsv"},
    "json": {"fn": to_json, "content_type": "application/json", "extension": ".json"},
    "zip": {"fn": to_zip, "content_type": "application/zip", "extension": ".zip"},
}
