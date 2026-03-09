"""Tests for the storage service."""


from app.services.storage_service import compute_sha256, validate_pdf


class TestValidatePdf:
    def test_valid_pdf_bytes(self, sample_pdf_bytes: bytes):
        assert validate_pdf(sample_pdf_bytes) is True

    def test_invalid_bytes(self, not_a_pdf: bytes):
        assert validate_pdf(not_a_pdf) is False

    def test_empty_bytes(self):
        assert validate_pdf(b"") is False

    def test_almost_pdf(self):
        # Starts with %PDF but too short
        assert validate_pdf(b"%PDF") is False


class TestComputeSha256:
    def test_deterministic(self, sample_pdf_bytes: bytes):
        h1 = compute_sha256(sample_pdf_bytes)
        h2 = compute_sha256(sample_pdf_bytes)
        assert h1 == h2
        assert len(h1) == 64  # hex digest length

    def test_different_content(self, sample_pdf_bytes: bytes, not_a_pdf: bytes):
        assert compute_sha256(sample_pdf_bytes) != compute_sha256(not_a_pdf)
