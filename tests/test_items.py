"""Tests for the items CRUD — happy path, ownership, and edge cases."""

from fastapi.testclient import TestClient


def test_create_and_list_items(client: TestClient, auth_headers: dict) -> None:
    response = client.post(
        "/items", json={"title": "First item"}, headers=auth_headers
    )
    assert response.status_code == 201
    item = response.json()
    assert item["title"] == "First item"
    assert item["done"] is False

    response = client.get("/items", headers=auth_headers)
    assert response.status_code == 200
    titles = [row["title"] for row in response.json()]
    assert "First item" in titles


def test_get_item_by_id(client: TestClient, auth_headers: dict) -> None:
    created = client.post(
        "/items", json={"title": "Get me"}, headers=auth_headers
    ).json()
    response = client.get(f"/items/{created['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Get me"


def test_get_missing_item_is_404(client: TestClient, auth_headers: dict) -> None:
    assert client.get("/items/999999", headers=auth_headers).status_code == 404


def test_delete_item_then_get_is_404(client: TestClient, auth_headers: dict) -> None:
    created = client.post(
        "/items", json={"title": "Delete me"}, headers=auth_headers
    ).json()
    assert client.delete(
        f"/items/{created['id']}", headers=auth_headers
    ).status_code == 204
    assert client.get(f"/items/{created['id']}", headers=auth_headers).status_code == 404


def test_delete_missing_item_is_404(client: TestClient, auth_headers: dict) -> None:
    assert client.delete("/items/999999", headers=auth_headers).status_code == 404


def test_items_require_auth(client: TestClient) -> None:
    assert client.get("/items").status_code == 401
    assert client.post("/items", json={"title": "Nope"}).status_code == 401


def test_create_item_rejects_empty_title(
    client: TestClient, auth_headers: dict
) -> None:
    response = client.post("/items", json={"title": ""}, headers=auth_headers)
    assert response.status_code == 422


def test_users_only_see_their_own_items(
    client: TestClient, auth_headers: dict
) -> None:
    """Items are owner-scoped: another user's item is a 404, not a leak."""
    import uuid

    other_email = f"other-{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/auth/register",
        json={"email": other_email, "password": "correct-horse-123"},
    )
    other_token = client.post(
        "/auth/login",
        data={"username": other_email, "password": "correct-horse-123"},
    ).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    mine = client.post(
        "/items", json={"title": "Private"}, headers=auth_headers
    ).json()
    assert client.get(f"/items/{mine['id']}", headers=other_headers).status_code == 404
    assert client.delete(
        f"/items/{mine['id']}", headers=other_headers
    ).status_code == 404
    # And the other user's list doesn't contain it either.
    titles = [
        row["title"] for row in client.get("/items", headers=other_headers).json()
    ]
    assert "Private" not in titles
