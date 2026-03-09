"""Tests for admin API endpoints in multi-user mode."""

from fastapi.testclient import TestClient

from app.models.user import User


class TestListUsers:
    def test_list_users_as_admin(
        self,
        multi_client: TestClient,
        admin_user: User,
        regular_user: User,
        admin_token: str,
    ):
        """Admin sees all users."""
        resp = multi_client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        usernames = [u["username"] for u in data["users"]]
        assert "admin" in usernames
        assert "alice" in usernames

    def test_list_users_as_non_admin(
        self,
        multi_client: TestClient,
        regular_user: User,
        user_token: str,
    ):
        """Non-admin gets 403."""
        resp = multi_client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403


class TestCreateUser:
    def test_create_user_as_admin(
        self,
        multi_client: TestClient,
        admin_user: User,
        admin_token: str,
    ):
        """Admin can create a new user."""
        resp = multi_client.post(
            "/api/admin/users",
            json={"username": "charlie", "password": "charliepass"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["username"] == "charlie"

    def test_create_user_as_non_admin(
        self,
        multi_client: TestClient,
        regular_user: User,
        user_token: str,
    ):
        """Non-admin gets 403."""
        resp = multi_client.post(
            "/api/admin/users",
            json={"username": "evil", "password": "evilpass"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403


class TestDeleteUser:
    def test_delete_user_as_admin(
        self,
        multi_client: TestClient,
        admin_user: User,
        regular_user: User,
        admin_token: str,
    ):
        """Admin can delete another user."""
        resp = multi_client.delete(
            f"/api/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 204

    def test_admin_cannot_delete_self(
        self,
        multi_client: TestClient,
        admin_user: User,
        admin_token: str,
    ):
        """Admin cannot delete their own account."""
        resp = multi_client.delete(
            f"/api/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400
        assert "Cannot delete yourself" in resp.json()["detail"]


class TestUpdateSettings:
    def test_update_settings_as_admin(
        self,
        multi_client: TestClient,
        admin_user: User,
        admin_token: str,
    ):
        """Admin can toggle allow_registration."""
        resp = multi_client.put(
            "/api/admin/settings?allow_registration=false",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["allow_registration"] is False

    def test_update_settings_as_non_admin(
        self,
        multi_client: TestClient,
        regular_user: User,
        user_token: str,
    ):
        """Non-admin gets 403."""
        resp = multi_client.put(
            "/api/admin/settings?allow_registration=false",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403
