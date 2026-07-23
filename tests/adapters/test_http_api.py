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
    assert client.get("/api/v1/search", params={"text": "ERP"}).json()["hits"]
    assert client.get("/api/v1/stats").json()["total_occurrences"] == 1

    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "TermKeeper API"
    assert "/api/v1/search" in schema["paths"]


def test_http_api_maps_application_and_request_errors() -> None:
    client = TestClient(create_app(TermKeeperService()))

    missing = client.get("/api/v1/meanings/999")
    assert missing.status_code == 404
    assert missing.json()["error"] == "NotFoundError"

    invalid = client.post("/api/v1/inbox", json={"keyword": " "})
    assert invalid.status_code == 422
    assert invalid.json()["error"] == "ValidationError"

    request_error = client.get("/api/v1/search", params={"text": "ERP", "limit": 0})
    assert request_error.status_code == 422
