from fastapi.testclient import TestClient

from termkeeper.adapters.http_api import create_app
from termkeeper.application import TermKeeperService


def test_http_api_workflow_and_openapi() -> None:
    client = TestClient(create_app())

    assert client.get("/health").json() == {"status": "ok"}
    captured = client.post(
        "/api/v1/inbox",
        json={"keyword": "ERP", "memo": "planning", "source": "Teams"},
    )
    assert captured.status_code == 201
    inbox_id = captured.json()["inbox"]["inbox_id"]
    assert client.get("/api/v1/inbox").json()[0]["keyword"] == "ERP"

    resolved = client.post(
        f"/api/v1/inbox/{inbox_id}/resolve",
        json={"full_name": "Enterprise Resource Planning"},
    )
    meaning_id = resolved.json()["meaning_id"]
    assert client.get(f"/api/v1/meanings/{meaning_id}").status_code == 200
    assert client.get("/api/v1/meanings").json()[0]["meaning_id"] == meaning_id
    assert (
        client.get(
            "/api/v1/meanings",
            params={"favorite_only": True},
        ).json()
        == []
    )

    updated = client.put(
        f"/api/v1/meanings/{meaning_id}",
        json={
            "full_name": "Enterprise Resource Planning System",
            "description": "Integrated business software",
        },
    )
    assert updated.json()["description"] == "Integrated business software"
    assert client.get("/api/v1/search", params={"text": "ERP"}).json()["hits"]
    assert client.get("/api/v1/stats").json()["total_occurrences"] == 1

    deleted = client.delete(f"/api/v1/meanings/{meaning_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get("/api/v1/meanings").json() == []
    assert client.get("/api/v1/trash").json()[0]["meaning_id"] == meaning_id

    restored = client.post(f"/api/v1/trash/{meaning_id}/restore")
    assert restored.json()["meaning_id"] == meaning_id
    assert client.get("/api/v1/trash").json() == []

    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "TermKeeper API"
    assert "/api/v1/search" in schema["paths"]
    assert set(schema["paths"]["/api/v1/meanings/{meaning_id}"]) == {
        "get",
        "put",
        "delete",
    }
    assert schema["paths"]["/api/v1/inbox"]["post"]["responses"]["201"]["content"][
        "application/json"
    ]["schema"] == {
        "$ref": "#/components/schemas/AddResult",
    }
    assert schema["paths"]["/api/v1/search"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"] == {
        "$ref": "#/components/schemas/SearchResult",
    }
    assert schema["components"]["schemas"]["Meaning"]["required"] == [
        "meaning_id",
        "public_id",
        "full_name",
        "description",
        "created_at",
        "updated_at",
    ]
    assert schema["components"]["schemas"]["ErrorResponse"]["required"] == [
        "error",
        "message",
    ]


def test_http_api_maps_application_and_request_errors() -> None:
    client = TestClient(create_app(TermKeeperService()))

    missing = client.get("/api/v1/meanings/999")
    assert missing.status_code == 404
    assert missing.json()["error"] == "NotFoundError"

    invalid = client.post("/api/v1/inbox", json={"keyword": " "})
    assert invalid.status_code == 422
    assert invalid.json()["error"] == "ValidationError"

    invalid_update = client.put(
        "/api/v1/meanings/999",
        json={"full_name": " "},
    )
    assert invalid_update.status_code == 422
    assert invalid_update.json()["error"] == "ValidationError"

    request_error = client.get("/api/v1/search", params={"text": "ERP", "limit": 0})
    assert request_error.status_code == 422
