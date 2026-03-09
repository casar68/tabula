"""API integration tests for template endpoints."""

from fastapi.testclient import TestClient

SAMPLE_TEMPLATE = {
    "name": "Test Template",
    "selections": [
        {
            "page": 1,
            "x1": 50.0,
            "y1": 100.0,
            "x2": 545.0,
            "y2": 230.0,
            "width": 495.0,
            "height": 130.0,
            "extraction_method": "guess",
        }
    ],
    "page_count": 1,
}


class TestTemplateCrud:
    def test_create_template(self, client: TestClient):
        response = client.post("/api/templates", json=SAMPLE_TEMPLATE)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Template"
        assert data["selection_count"] == 1
        assert data["page_count"] == 1
        assert "id" in data

    def test_list_templates(self, client: TestClient):
        # Create one
        client.post("/api/templates", json=SAMPLE_TEMPLATE)
        # List
        response = client.get("/api/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data["templates"]) == 1

    def test_get_template(self, client: TestClient):
        create_resp = client.post("/api/templates", json=SAMPLE_TEMPLATE)
        template_id = create_resp.json()["id"]

        response = client.get(f"/api/templates/{template_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Template"

    def test_update_template(self, client: TestClient):
        create_resp = client.post("/api/templates", json=SAMPLE_TEMPLATE)
        template_id = create_resp.json()["id"]

        response = client.put(
            f"/api/templates/{template_id}",
            json={"name": "Renamed"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Renamed"

    def test_delete_template(self, client: TestClient):
        create_resp = client.post("/api/templates", json=SAMPLE_TEMPLATE)
        template_id = create_resp.json()["id"]

        response = client.delete(f"/api/templates/{template_id}")
        assert response.status_code == 200

        # Verify gone
        get_resp = client.get(f"/api/templates/{template_id}")
        assert get_resp.status_code == 404

    def test_export_template(self, client: TestClient):
        create_resp = client.post("/api/templates", json=SAMPLE_TEMPLATE)
        template_id = create_resp.json()["id"]

        response = client.get(f"/api/templates/{template_id}/export")
        assert response.status_code == 200
        assert "Content-Disposition" in response.headers
        data = response.json()
        assert data["name"] == "Test Template"
        assert "template" in data

    def test_get_nonexistent(self, client: TestClient):
        response = client.get("/api/templates/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
