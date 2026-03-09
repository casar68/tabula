"""Tests for the extraction service."""

from pathlib import Path

import pytest

from app.services.extraction_service import (
    _cluster_words_into_rows,
    _detect_columns_from_coverage,
    _is_garbled,
    detect_tables,
    extract_tables,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# _is_garbled
# ---------------------------------------------------------------------------

class TestIsGarbled:
    def test_normal_text_is_not_garbled(self):
        assert _is_garbled("Hello world, this is a normal sentence.") is False

    def test_french_text_is_not_garbled(self):
        assert _is_garbled("Rémunération brute : 2 500,00 euros") is False

    def test_garbled_text_is_detected(self):
        # Simulate garbled font encoding output
        garbled = "\uf001\uf002\uf003\uf004\uf005\uf006\uf007\uf008\uf009\uf00a\uf00b"
        assert _is_garbled(garbled) is True

    def test_short_text_is_not_garbled(self):
        # Less than 10 chars => always False
        assert _is_garbled("abc") is False

    def test_empty_text_is_not_garbled(self):
        assert _is_garbled("") is False

    def test_mixed_text_below_threshold(self):
        # Lots of unusual characters mixed with normal ones
        text = "abc" + "\uf001" * 20
        assert _is_garbled(text) is True


# ---------------------------------------------------------------------------
# _cluster_words_into_rows
# ---------------------------------------------------------------------------

class TestClusterWordsIntoRows:
    def _word(self, text, left, top, width=50, height=15):
        return {"text": text, "left": left, "top": top, "width": width, "height": height}

    def test_empty_input(self):
        assert _cluster_words_into_rows([]) == []

    def test_single_row(self):
        words = [
            self._word("hello", 10, 100),
            self._word("world", 70, 102),
        ]
        rows = _cluster_words_into_rows(words)
        assert len(rows) == 1
        assert len(rows[0]) == 2

    def test_two_rows(self):
        words = [
            self._word("row1-a", 10, 100),
            self._word("row1-b", 70, 102),
            self._word("row2-a", 10, 140),
            self._word("row2-b", 70, 141),
        ]
        rows = _cluster_words_into_rows(words)
        assert len(rows) == 2
        assert len(rows[0]) == 2
        assert len(rows[1]) == 2

    def test_rows_are_sorted_top_to_bottom(self):
        words = [
            self._word("bottom", 10, 200),
            self._word("top", 10, 50),
            self._word("middle", 10, 120),
        ]
        rows = _cluster_words_into_rows(words)
        assert len(rows) == 3
        assert rows[0][0]["text"] == "top"
        assert rows[1][0]["text"] == "middle"
        assert rows[2][0]["text"] == "bottom"


# ---------------------------------------------------------------------------
# _detect_columns_from_coverage
# ---------------------------------------------------------------------------

class TestDetectColumnsFromCoverage:
    def _word(self, text, left, width=40, top=0, height=15):
        return {"text": text, "left": left, "top": top, "width": width, "height": height}

    def test_empty_rows(self):
        bounds = _detect_columns_from_coverage([], 500)
        assert bounds == [0, 500]

    def test_single_column(self):
        # All words in the same x region
        rows = [
            [self._word("a", 10, top=i * 20)] for i in range(10)
        ]
        bounds = _detect_columns_from_coverage(rows, 200)
        # Should have at least 2 boundaries (start, end)
        assert len(bounds) >= 2
        assert bounds[0] == 0

    def test_two_clear_columns(self):
        # Words at x=10-50 and x=300-340, big gap in between
        rows = []
        for i in range(20):
            rows.append([
                self._word("left", 10, top=i * 20),
                self._word("right", 300, top=i * 20),
            ])
        bounds = _detect_columns_from_coverage(rows, 500)
        # Should detect at least one column separator between 50 and 300
        assert len(bounds) >= 3
        separators = bounds[1:-1]
        assert any(50 < s < 300 for s in separators)


# ---------------------------------------------------------------------------
# extract_tables / detect_tables (integration with test PDF)
# ---------------------------------------------------------------------------

class TestExtractAndDetectTables:
    def test_detect_tables_finds_table(self):
        pdf_path = FIXTURES_DIR / "simple_table.pdf"
        if not pdf_path.exists():
            pytest.skip("Test PDF fixture not available")

        tables = detect_tables(pdf_path)
        assert len(tables) >= 1
        first = tables[0]
        assert first["page"] == 1
        assert "x1" in first
        assert "y1" in first
        assert first["width"] > 0
        assert first["height"] > 0

    def test_extract_tables_returns_data(self):
        from app.schemas.extraction import ExtractionSelection

        pdf_path = FIXTURES_DIR / "simple_table.pdf"
        if not pdf_path.exists():
            pytest.skip("Test PDF fixture not available")

        selections = [
            ExtractionSelection(
                page=1, x1=50, y1=100, x2=545, y2=230,
                extraction_method="guess",
            )
        ]
        results = extract_tables(pdf_path, selections)
        assert len(results) == 1
        assert results[0]["page"] == 1
        data = results[0]["data"]
        assert len(data) >= 1  # At least one row
