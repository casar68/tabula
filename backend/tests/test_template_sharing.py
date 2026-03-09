"""Tests for template sharing in multi-user mode."""

from fastapi.testclient import TestClient

from app.models.user import User

TEMPLATE_DATA = {
    "name": "Test Template",
    "page_count": 1,
    "selections": [
        {
            "page": 1,
            "extraction_method": "lattice",
            "x1": 0,
            "y1": 0,
            "x2": 100,
            "y2": 100,
            "width": 100,
            "height": 100,
        }
    ],
}


class TestTemplateSharing:
    """Verify template visibility and ownership rules."""

    def test_user_sees_own_templates(
        self,
        multi_client: TestClient,
        regular_user: User,
        second_user: User,
        user_token: str,
        second_user_token: str,
    ):
        """Alice creates a template; bob does not see it."""
        multi_client.post(
            "/api/templates",
            json=TEMPLATE_DATA,
            headers={"Authorization": f"Bearer {user_token}"},
        )

        resp = multi_client.get(
            "/api/templates",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["templates"]) == 0

    def test_shared_template_visible_to_all(
        self,
        multi_client: TestClient,
        admin_user: User,
        regular_user: User,
        second_user: User,
        admin_token: str,
        user_token: str,
        second_user_token: str,
    ):
        """Once marked shared by admin, bob sees alice's template."""
        # Alice creates
        resp = multi_client.post(
            "/api/templates",
            json=TEMPLATE_DATA,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        template_id = resp.json()["id"]

        # Admin marks shared
        resp = multi_client.put(
            f"/api/templates/{template_id}/share",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_shared"] is True

        # Bob lists
        resp = multi_client.get(
            "/api/templates",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )
        assert len(resp.json()["templates"]) == 1

    def test_non_owner_cannot_modify_shared_template(
        self,
        multi_client: TestClient,
        admin_user: User,
        regular_user: User,
        second_user: User,
        admin_token: str,
        user_token: str,
        second_user_token: str,
    ):
        """Bob cannot PUT a shared template he doesn't own."""
        resp = multi_client.post(
            "/api/templates",
            json=TEMPLATE_DATA,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        template_id = resp.json()["id"]

        # Admin shares it
        multi_client.put(
            f"/api/templates/{template_id}/share",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Bob tries to modify
        resp = multi_client.put(
            f"/api/templates/{template_id}",
            json={"name": "Hacked"},
            headers={"Authorization": f"Bearer {second_user_token}"},
        )
        assert resp.status_code == 403

    def test_non_owner_cannot_delete_shared_template(
        self,
        multi_client: TestClient,
        admin_user: User,
        regular_user: User,
        second_user: User,
        admin_token: str,
        user_token: str,
        second_user_token: str,
    ):
        """Bob cannot DELETE a shared template he doesn't own."""
        resp = multi_client.post(
            "/api/templates",
            json=TEMPLATE_DATA,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        template_id = resp.json()["id"]

        multi_client.put(
            f"/api/templates/{template_id}/share",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        resp = multi_client.delete(
            f"/api/templates/{template_id}",
            headers={"Authorization": f"Bearer {second_user_token}"},
        )
        assert resp.status_code == 403

    def test_admin_can_toggle_share(
        self,
        multi_client: TestClient,
        admin_user: User,
        regular_user: User,
        admin_token: str,
        user_token: str,
    ):
        """Admin toggles shared status on and off."""
        resp = multi_client.post(
            "/api/templates",
            json=TEMPLATE_DATA,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        template_id = resp.json()["id"]

        # Share
        resp = multi_client.put(
            f"/api/templates/{template_id}/share",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["is_shared"] is True

        # Unshare
        resp = multi_client.put(
            f"/api/templates/{template_id}/share",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["is_shared"] is False

    def test_non_admin_cannot_toggle_share(
        self,
        multi_client: TestClient,
        regular_user: User,
        user_token: str,
    ):
        """Non-admin cannot call PUT /share."""
        resp = multi_client.post(
            "/api/templates",
            json=TEMPLATE_DATA,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        template_id = resp.json()["id"]

        resp = multi_client.put(
            f"/api/templates/{template_id}/share",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403
