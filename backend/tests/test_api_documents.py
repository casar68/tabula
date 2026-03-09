"""API integration tests for document endpoints."""

import io
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestUploadDocuments:
    @patch("app.api.documents.get_executor")
    def test_upload_valid_pdf(self, mock_executor, client: TestClient, sample_pdf_bytes: bytes):
        response = client.post(
            "/api/documents/upload",
            files=[("files", ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))],
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["uploads"]) == 1
        assert data["uploads"][0]["original_filename"] == "test.pdf"
        assert "id" in data["uploads"][0]
        assert "job_id" in data["uploads"][0]
        # Verify a background job was queued
        assert mock_executor.return_value.submit.called

    def test_upload_invalid_file(self, client: TestClient, not_a_pdf: bytes):
        response = client.post(
            "/api/documents/upload",
            files=[("files", ("bad.pdf", io.BytesIO(not_a_pdf), "application/pdf"))],
        )
        assert response.status_code == 400
        assert "not a valid PDF" in response.json()["detail"]

    def test_upload_too_large(self, client: TestClient):
        # Create content just over 100MB
        # We patch MAX_UPLOAD_SIZE to a small value instead
        from app.api import documents
        original = documents.MAX_UPLOAD_SIZE
        documents.MAX_UPLOAD_SIZE = 100  # 100 bytes

        try:
            # A valid PDF header but content exceeds 100 bytes
            content = b"%PDF-1.4" + b"\x00" * 200
            response = client.post(
                "/api/documents/upload",
                files=[("files", ("big.pdf", io.BytesIO(content), "application/pdf"))],
            )
            assert response.status_code == 413
            assert "exceeds" in response.json()["detail"]
        finally:
            documents.MAX_UPLOAD_SIZE = original


class TestListDocuments:
    def test_empty_list(self, client: TestClient):
        response = client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total"] == 0

    @patch("app.api.documents.get_executor")
    def test_list_after_upload(self, mock_executor, client: TestClient, sample_pdf_bytes: bytes):
        # Upload a file first
        client.post(
            "/api/documents/upload",
            files=[("files", ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))],
        )
        response = client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 1
        assert data["total"] == 1

    def test_pagination_params(self, client: TestClient):
        response = client.get("/api/documents?offset=0&limit=10")
        assert response.status_code == 200


class TestDeleteDocument:
    @patch("app.api.documents.get_executor")
    def test_delete_existing(self, mock_executor, client: TestClient, sample_pdf_bytes: bytes):
        # Upload
        upload_resp = client.post(
            "/api/documents/upload",
            files=[("files", ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))],
        )
        doc_id = upload_resp.json()["uploads"][0]["id"]

        # Delete
        response = client.delete(f"/api/documents/{doc_id}")
        assert response.status_code == 200

        # Verify it's gone
        get_resp = client.get(f"/api/documents/{doc_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent(self, client: TestClient):
        response = client.delete("/api/documents/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestGetDocument:
    @patch("app.api.documents.get_executor")
    def test_get_existing(self, mock_executor, client: TestClient, sample_pdf_bytes: bytes):
        upload_resp = client.post(
            "/api/documents/upload",
            files=[("files", ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))],
        )
        doc_id = upload_resp.json()["uploads"][0]["id"]

        response = client.get(f"/api/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["original_filename"] == "test.pdf"
        assert data["file_size"] > 0

    def test_get_nonexistent(self, client: TestClient):
        response = client.get("/api/documents/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
