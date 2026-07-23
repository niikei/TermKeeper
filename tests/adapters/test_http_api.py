from fastapi.testclient import TestClient

from termkeeper.adapters.http import create_app
from termkeeper.application import TermKeeperService
from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.tables import Occurrence


def test_http_api_workflow_and_openapi() -> None:
    client = TestClient(create_app())
    public_id = _exercise_core_workflow(client)
    _exercise_metadata_workflow(client, public_id)
    _exercise_lifecycle_workflow(client, public_id)
    _assert_openapi_contract(client)


def _exercise_core_workflow(client: TestClient) -> str:
    assert client.get("/health").json() == {"status": "ok"}
    sap_scope_id = client.post("/api/v1/scopes", json={"name": "SAP"}).json()["public_id"]
    s4_scope_id = client.post(
        "/api/v1/scopes",
        json={"name": "SAP S/4HANA"},
    ).json()["public_id"]
    captured = client.post(
        "/api/v1/occurrences",
        json={"keyword": "ERP", "memo": "planning", "source": "Teams"},
    )
    assert captured.status_code == 201
    occurrence_id = captured.json()["occurrence"]["public_id"]
    assert captured.json()["occurrence"]["status"] == "Pending"
    assert captured.json()["occurrence"]["occurred_at"].endswith("Z")
    assert captured.json()["occurrence"]["updated_at"].endswith("Z")
    assert captured.json()["candidates"] == []
    inbox_page = client.get("/api/v1/inbox").json()
    assert inbox_page["items"][0]["keyword"] == "ERP"
    assert inbox_page["has_more"] is False

    resolved = client.post(
        f"/api/v1/occurrences/{occurrence_id}/resolve",
        json={
            "full_name": "Enterprise Resource Planning",
            "scope_id": sap_scope_id,
        },
    )
    public_id = resolved.json()["public_id"]
    assert resolved.json()["scope"] == "SAP"
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
            "scope_id": s4_scope_id,
            "description": "Integrated business software",
        },
    )
    assert updated.json()["description"] == "Integrated business software"
    assert updated.json()["scope"] == "SAP S/4HANA"
    assert client.get("/api/v1/search", params={"text": "ERP"}).json()["hits"]
    assert client.get("/api/v1/stats").json()["total_occurrences"] == 1

    occurrences = client.get(
        "/api/v1/occurrences",
        params={"meaning_id": public_id, "status": "Resolved"},
    ).json()
    occurrence_id = occurrences["items"][0]["public_id"]
    occurrence = client.put(
        f"/api/v1/occurrences/{occurrence_id}",
        json={"memo": "Updated through HTTP"},
    )
    assert occurrence.json()["memo"] == "Updated through HTTP"
    assert occurrence.json()["occurred_at"].endswith("Z")
    assert occurrence.json()["updated_at"].endswith("Z")

    assert (
        client.post(f"/api/v1/occurrences/{occurrence_id}/unresolve").json()["status"] == "Pending"
    )
    assigned = client.post(
        f"/api/v1/occurrences/{occurrence_id}/assign/{public_id}",
    ).json()
    assert assigned["meaning_id"] == public_id
    client.post(f"/api/v1/occurrences/{occurrence_id}/unresolve")
    assert (
        client.post(f"/api/v1/occurrences/{occurrence_id}/discard").json()["status"] == "Discarded"
    )
    assert client.post(f"/api/v1/occurrences/{occurrence_id}/reopen").json()["status"] == "Pending"
    client.post(f"/api/v1/occurrences/{occurrence_id}/assign/{public_id}")
    return public_id


def _exercise_metadata_workflow(client: TestClient, public_id: str) -> None:
    assert client.put(f"/api/v1/meanings/{public_id}/tags/SAP").json()["tags"] == ["SAP"]
    assert client.get("/api/v1/tags").json()["items"][0]["name"] == "SAP"
    assert client.delete(f"/api/v1/meanings/{public_id}/tags/SAP").json()["tags"] == []
    assert client.put(f"/api/v1/meanings/{public_id}/favorite").json()["is_favorite"] is True
    assert client.delete(f"/api/v1/meanings/{public_id}/favorite").json()["is_favorite"] is False

    second_capture = client.post("/api/v1/occurrences", json={"keyword": "MRP"}).json()
    second = client.post(
        f"/api/v1/occurrences/{second_capture['occurrence']['public_id']}/resolve",
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
    assert schema["paths"]["/api/v1/occurrences"]["post"]["responses"]["201"]["content"][
        "application/json"
    ]["schema"] == {
        "$ref": "#/components/schemas/ExternalCaptureResult",
    }
    assert schema["paths"]["/api/v1/search"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"] == {
        "$ref": "#/components/schemas/ExternalSearchResult",
    }
    assert schema["components"]["schemas"]["ExternalMeaning"]["required"] == [
        "public_id",
        "full_name",
        "scope_id",
        "scope",
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
    assert schema["paths"]["/api/v1/search"]["get"]["responses"]["422"]["content"][
        "application/json"
    ]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse",
    }
    meaning_parameter = schema["paths"]["/api/v1/meanings/{meaning_id}"]["get"]["parameters"][0]
    assert meaning_parameter["schema"]["format"] == "uuid"


def test_http_api_maps_application_and_request_errors() -> None:
    client = TestClient(create_app(TermKeeperService()))

    missing = client.get("/api/v1/meanings/00000000-0000-0000-0000-000000000999")
    assert missing.status_code == 404
    assert set(missing.json()) == {"error", "message"}
    assert missing.json()["error"] == "NotFoundError"

    invalid = client.post("/api/v1/occurrences", json={"keyword": " "})
    assert invalid.status_code == 422
    assert invalid.json() == {
        "error": "ValidationError",
        "message": "Keyword must not be empty.",
    }

    captured = client.post("/api/v1/occurrences", json={"keyword": "ERP"}).json()
    resolved = client.post(
        f"/api/v1/occurrences/{captured['occurrence']['public_id']}/resolve",
        json={
            "full_name": "Enterprise Resource Planning",
        },
    ).json()
    invalid_update = client.put(
        f"/api/v1/meanings/{resolved['public_id']}",
        json={
            "full_name": " ",
            "scope_id": resolved["scope_id"],
        },
    )
    assert invalid_update.status_code == 422
    assert invalid_update.json()["error"] == "ValidationError"

    request_errors = (
        (
            client.get("/api/v1/search", params={"text": "ERP", "limit": 0}),
            ["query", "limit"],
            "greater_than_equal",
        ),
        (
            client.get("/api/v1/meanings/not-a-uuid"),
            ["path", "meaning_id"],
            "uuid_parsing",
        ),
        (
            client.post("/api/v1/occurrences", json={}),
            ["body", "keyword"],
            "missing",
        ),
    )
    for response, location, code in request_errors:
        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "RequestValidationError"
        assert body["message"] == "Request validation failed."
        assert body["details"][0]["location"] == location
        assert body["details"][0]["code"] == code
        assert body["details"][0]["message"]


def test_http_scope_lifecycle_uses_stable_ids() -> None:
    client = TestClient(create_app())

    created = client.post(
        "/api/v1/scopes",
        json={"name": "SAP", "description": "Enterprise platform"},
    )
    assert created.status_code == 201
    scope_id = created.json()["public_id"]
    assert client.get("/api/v1/scopes").json()["items"][1]["public_id"] == scope_id

    updated = client.put(
        f"/api/v1/scopes/{scope_id}",
        json={"name": "SAP S/4HANA", "description": "Current platform"},
    )
    assert updated.json()["public_id"] == scope_id
    assert updated.json()["name"] == "SAP S/4HANA"

    deleted = client.delete(f"/api/v1/scopes/{scope_id}")
    assert deleted.status_code == 204


def test_http_occurrence_pages_reach_beyond_500() -> None:
    with get_session() as session:
        session.add_all(
            [
                Occurrence(keyword=f"TERM-{index}", keyword_norm=f"term-{index}")
                for index in range(505)
            ],
        )
        session.commit()
    client = TestClient(create_app())

    first = client.get("/api/v1/inbox", params={"limit": 100}).json()
    tail = client.get(
        "/api/v1/occurrences",
        params={"offset": 500, "limit": 10},
    ).json()

    assert len(first["items"]) == 100
    assert first["has_more"] is True
    assert len(tail["items"]) == 5
    assert tail["offset"] == 500
    assert tail["has_more"] is False
