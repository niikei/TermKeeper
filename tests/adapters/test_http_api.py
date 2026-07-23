from fastapi.testclient import TestClient

from termkeeper.adapters.http_api import create_app
from termkeeper.application import TermKeeperService


def test_http_api_workflow_and_openapi() -> None:
    client = TestClient(create_app())
    public_id = _exercise_core_workflow(client)
    _exercise_metadata_workflow(client, public_id)
    _exercise_lifecycle_workflow(client, public_id)
    _assert_openapi_contract(client)


def _exercise_core_workflow(client: TestClient) -> str:

    assert client.get("/health").json() == {"status": "ok"}
    captured = client.post(
        "/api/v1/inbox",
        json={"keyword": "ERP", "memo": "planning", "source": "Teams"},
    )
    assert captured.status_code == 201
    inbox_public_id = captured.json()["inbox"]["public_id"]
    inbox_page = client.get("/api/v1/inbox").json()
    assert inbox_page["items"][0]["keyword"] == "ERP"
    assert inbox_page["has_more"] is False

    resolved = client.post(
        f"/api/v1/inbox/{inbox_public_id}/resolve",
        json={"full_name": "Enterprise Resource Planning"},
    )
    public_id = resolved.json()["public_id"]
    assert "meaning_id" not in resolved.json()
    assert client.get(f"/api/v1/meanings/{public_id}").status_code == 200
    assert client.get("/api/v1/meanings").json()["items"][0]["public_id"] == public_id
    assert (
        client.get(
            "/api/v1/meanings",
            params={"favorite_only": True},
        ).json()["items"]
        == []
    )

    updated = client.put(
        f"/api/v1/meanings/{public_id}",
        json={
            "full_name": "Enterprise Resource Planning System",
            "description": "Integrated business software",
        },
    )
    assert updated.json()["description"] == "Integrated business software"
    assert client.get("/api/v1/search", params={"text": "ERP"}).json()["hits"]
    assert client.get("/api/v1/stats").json()["total_occurrences"] == 1

    occurrences = client.get(
        "/api/v1/occurrences",
        params={"meaning_id": public_id},
    ).json()
    occurrence_id = occurrences["items"][0]["public_id"]
    occurrence = client.put(
        f"/api/v1/occurrences/{occurrence_id}",
        json={"memo": "Updated through HTTP"},
    )
    assert occurrence.json()["memo"] == "Updated through HTTP"
    return public_id


def _exercise_metadata_workflow(client: TestClient, public_id: str) -> None:
    assert client.put(f"/api/v1/meanings/{public_id}/tags/SAP").json()["tags"] == ["SAP"]
    assert client.get("/api/v1/tags").json()["items"][0]["name"] == "SAP"
    assert client.delete(f"/api/v1/meanings/{public_id}/tags/SAP").json()["tags"] == []
    assert client.put(f"/api/v1/meanings/{public_id}/favorite").json()["is_favorite"] is True
    assert client.delete(f"/api/v1/meanings/{public_id}/favorite").json()["is_favorite"] is False

    second_capture = client.post("/api/v1/inbox", json={"keyword": "MRP"}).json()
    second = client.post(
        f"/api/v1/inbox/{second_capture['inbox']['public_id']}/resolve",
        json={"full_name": "Material Requirements Planning"},
    ).json()
    first_page = client.get("/api/v1/meanings", params={"limit": 1}).json()
    assert len(first_page["items"]) == 1
    assert first_page["has_more"] is True
    second_page = client.get(
        "/api/v1/meanings",
        params={"offset": 1, "limit": 1},
    ).json()
    assert len(second_page["items"]) == 1
    assert second_page["has_more"] is False
    related = client.put(
        f"/api/v1/meanings/{public_id}/related/{second['public_id']}",
    ).json()
    assert related[0]["public_id"] == second["public_id"]
    assert (
        client.get(
            f"/api/v1/meanings/{public_id}/related",
        ).json()["items"][0]["public_id"]
        == second["public_id"]
    )
    assert (
        client.delete(
            f"/api/v1/meanings/{public_id}/related/{second['public_id']}",
        ).json()
        == []
    )

    reference = client.post(
        f"/api/v1/meanings/{public_id}/references",
        json={"url": "https://example.com/erp", "title": "ERP guide"},
    ).json()
    assert (
        client.get(
            f"/api/v1/meanings/{public_id}/references",
        ).json()["items"][0]["public_id"]
        == reference["public_id"]
    )
    assert (
        client.put(
            f"/api/v1/references/{reference['public_id']}",
            json={"title": "Updated guide"},
        ).json()["title"]
        == "Updated guide"
    )
    assert (
        client.delete(
            f"/api/v1/references/{reference['public_id']}",
        ).json()["public_id"]
        == reference["public_id"]
    )


def _exercise_lifecycle_workflow(client: TestClient, public_id: str) -> None:
    deleted = client.delete(f"/api/v1/meanings/{public_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert all(
        item["public_id"] != public_id for item in client.get("/api/v1/meanings").json()["items"]
    )
    assert client.get("/api/v1/trash").json()["items"][0]["public_id"] == public_id

    restored = client.post(f"/api/v1/trash/{public_id}/restore")
    assert restored.json()["public_id"] == public_id
    assert client.get("/api/v1/trash").json()["items"] == []


def _assert_openapi_contract(client: TestClient) -> None:
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
        "$ref": "#/components/schemas/ExternalAddResult",
    }
    assert schema["paths"]["/api/v1/search"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"] == {
        "$ref": "#/components/schemas/ExternalSearchResult",
    }
    assert schema["components"]["schemas"]["ExternalMeaning"]["required"] == [
        "public_id",
        "full_name",
        "description",
        "created_at",
        "updated_at",
        "deleted_at",
        "is_favorite",
        "terms",
        "tags",
    ]
    assert schema["components"]["schemas"]["ErrorResponse"]["required"] == [
        "error",
        "message",
    ]
    meaning_parameter = schema["paths"]["/api/v1/meanings/{meaning_id}"]["get"]["parameters"][0]
    assert meaning_parameter["schema"]["format"] == "uuid"


def test_http_api_maps_application_and_request_errors() -> None:
    client = TestClient(create_app(TermKeeperService()))

    missing = client.get("/api/v1/meanings/00000000-0000-0000-0000-000000000999")
    assert missing.status_code == 404
    assert missing.json()["error"] == "NotFoundError"

    invalid = client.post("/api/v1/inbox", json={"keyword": " "})
    assert invalid.status_code == 422
    assert invalid.json()["error"] == "ValidationError"

    captured = client.post("/api/v1/inbox", json={"keyword": "ERP"}).json()
    resolved = client.post(
        f"/api/v1/inbox/{captured['inbox']['public_id']}/resolve",
        json={"full_name": "Enterprise Resource Planning"},
    ).json()
    invalid_update = client.put(
        f"/api/v1/meanings/{resolved['public_id']}",
        json={"full_name": " "},
    )
    assert invalid_update.status_code == 422
    assert invalid_update.json()["error"] == "ValidationError"

    request_error = client.get("/api/v1/search", params={"text": "ERP", "limit": 0})
    assert request_error.status_code == 422

    invalid_identifier = client.get("/api/v1/meanings/not-a-uuid")
    assert invalid_identifier.status_code == 422

    invalid_inbox_identifier = client.post(
        "/api/v1/inbox/not-a-uuid/resolve",
        json={"full_name": "Enterprise Resource Planning"},
    )
    assert invalid_inbox_identifier.status_code == 422
