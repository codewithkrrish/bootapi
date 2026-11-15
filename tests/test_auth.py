"""Tests for register / login / me, including the unhappy paths."""

import uuid

from fastapi.testclient import TestClient


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


def test_register_returns_user_without_password(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": _email(), "password": "correct-horse-123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"].endswith("@example.com")
    assert isinstance(body["id"], int)
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    email = _email()
    assert client.post(
        "/auth/register", json={"email": email, "password": "correct-horse-123"}
    ).status_code == 201
    response = client.post(
        "/auth/register", json={"email": email, "password": "another-pass-123"}
    )
    assert response.status_code == 409


def test_register_rejects_bad_email_and_short_password(client: TestClient) -> None:
    assert client.post(
        "/auth/register", json={"email": "not-an-email", "password": "correct-horse-123"}
    ).status_code == 422
    assert client.post(
        "/auth/register", json={"email": _email(), "password": "short"}
    ).status_code == 422


def test_login_returns_bearer_token(client: TestClient) -> None:
    email = _email()
    client.post(
        "/auth/register", json={"email": email, "password": "correct-horse-123"}
    )
    response = client.post(
        "/auth/login", data={"username": email, "password": "correct-horse-123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_is_401(client: TestClient) -> None:
    email = _email()
    client.post(
        "/auth/register", json={"email": email, "password": "correct-horse-123"}
    )
    response = client.post(
        "/auth/login", data={"username": email, "password": "wrong-password-123"}
    )
    assert response.status_code == 401


def test_login_unknown_email_is_401(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        data={"username": _email(), "password": "correct-horse-123"},
    )
    assert response.status_code == 401


def test_me_returns_current_user(client: TestClient, auth_headers: dict) -> None:
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"].endswith("@example.com")


def test_me_without_token_is_401(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401


def test_me_with_garbage_token_is_401(client: TestClient) -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer nope"})
    assert response.status_code == 401
