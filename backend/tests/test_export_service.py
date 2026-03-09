"""Tests for the export service."""

import csv
import io
import json
import zipfile

from app.services.export_service import to_csv, to_json, to_tsv, to_zip

SAMPLE_TABLES = [
    {
        "spec_index": 0,
        "page": 1,
        "data": [
            ["Name", "Value", "Unit"],
            ["Temperature", "25.3", "Celsius"],
            ["Pressure", "1013.25", "hPa"],
        ],
    }
]

TWO_TABLES = [
    {
        "spec_index": 0,
        "page": 1,
        "data": [["A", "B"], ["1", "2"]],
    },
    {
        "spec_index": 1,
        "page": 2,
        "data": [["C", "D"], ["3", "4"]],
    },
]


class TestToCsv:
    def test_basic_csv(self):
        result = to_csv(SAMPLE_TABLES)
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 3
        assert rows[0] == ["Name", "Value", "Unit"]
        assert rows[1] == ["Temperature", "25.3", "Celsius"]

    def test_multiple_tables_separated(self):
        result = to_csv(TWO_TABLES)
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        # 2 rows from table 1 + 1 empty separator + 2 rows from table 2 + trailing empty
        non_trailing = [r for r in rows if r]  # filter trailing empty rows
        assert len(non_trailing) == 4  # 4 data rows total
        # Check separator exists between tables
        assert [] in rows


class TestToTsv:
    def test_basic_tsv(self):
        result = to_tsv(SAMPLE_TABLES)
        assert "\t" in result
        lines = result.strip().splitlines()
        assert len(lines) == 3
        # csv writer may add \r on some platforms; strip each line
        assert lines[0].strip().split("\t") == ["Name", "Value", "Unit"]


class TestToJson:
    def test_basic_json(self):
        result = to_json(SAMPLE_TABLES)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["page"] == 1
        assert len(parsed[0]["data"]) == 3


class TestToZip:
    def test_basic_zip(self):
        result = to_zip(SAMPLE_TABLES, "test")
        assert isinstance(result, bytes)
        zf = zipfile.ZipFile(io.BytesIO(result))
        names = zf.namelist()
        assert len(names) == 1
        assert "test-page1-table1.csv" in names[0]

    def test_multiple_tables_zip(self):
        result = to_zip(TWO_TABLES, "multi")
        zf = zipfile.ZipFile(io.BytesIO(result))
        assert len(zf.namelist()) == 2
