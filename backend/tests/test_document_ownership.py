"""Tests for document ownership and isolation in multi-user mode."""

import io
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.models.user import User


class TestDocumentOwnership:
    """Verify that documents are properly isolated between users."""

    @patch("app.api.documents.get_executor")
    def test_user_sees_own_documents(
        self,
        mock_executor,
        multi_client: TestClient,
        regular_user: User,
        second_user: User,
        user_token: str,
        second_user_token: str,
        sample_pdf_bytes: bytes,
    ):
        """Alice uploads a doc; bob's list is empty."""
        # Alice uploads
        multi_client.post(
            "/api/documents/upload",
            files=[("files", ("alice.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))],
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Bob lists -- should be empty
        resp = multi_client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @patch("app.api.documents.get_executor")
    def test_user_cannot_access_other_users_document(
        self,
        mock_executor,
        multi_client: TestClient,
        regular_user: User,
        second_user: User,
        user_token: str,
        second_user_token: str,
        sample_pdf_bytes: bytes,
    ):
        """Bob cannot GET alice's document."""
        resp = multi_client.post(
            "/api/documents/upload",
            files=[("files", ("alice.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))],
            headers={"Authorization": f"Bearer {user_token}"},
        )
        doc_id = resp.json()["uploads"][0]["id"]

        resp = multi_client.get(
            f"/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )
        assert resp.status_code == 404

    @patch("app.api.documents.get_executor")
    def test_user_cannot_delete_other_users_document(
        self,
        mock_executor,
        multi_client: TestClient,
        regular_user: User,
        second_user: User,
        user_token: str,
        second_user_token: str,
        sample_pdf_bytes: bytes,
    ):
        """Bob cannot DELETE alice's document."""
        resp = multi_client.post(
            "/api/documents/upload",
            files=[("files", ("alice.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))],
            headers={"Authorization": f"Bearer {user_token}"},
        )
        doc_id = resp.json()["uploads"][0]["id"]

        resp = multi_client.delete(
            f"/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )
        assert resp.status_code == 404

    @patch("app.api.documents.get_executor")
    def test_admin_sees_all_documents(
        self,
        mock_executor,
        multi_client: TestClient,
        admin_user: User,
        regular_user: User,
        admin_token: str,
        user_token: str,
        sample_pdf_bytes: bytes,
    ):
        """Admin can list documents from all users."""
        # Alice uploads
        multi_client.post(
            "/api/documents/upload",
            files=[("files", ("alice.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))],
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Admin lists -- should see alice's doc
        resp = multi_client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    @patch("app.api.documents.get_executor")
    def test_admin_can_delete_any_document(
        self,
        mock_executor,
        multi_client: TestClient,
        admin_user: User,
        regular_user: User,
        admin_token: str,
        user_token: str,
        sample_pdf_bytes: bytes,
    ):
        """Admin can delete alice's document."""
        resp = multi_client.post(
            "/api/documents/upload",
            files=[("files", ("alice.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))],
            headers={"Authorization": f"Bearer {user_token}"},
        )
        doc_id = resp.json()["uploads"][0]["id"]

        resp = multi_client.delete(
            f"/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    def test_unauthenticated_request_rejected(
        self,
        multi_client: TestClient,
    ):
        """Request without Authorization header returns 401."""
        resp = multi_client.get("/api/documents")
        assert resp.status_code == 401
