"""Shared fixtures for the bootapi test suite.

Tests run against a throwaway SQLite file in a temp dir — the env var is
set before the app is imported, so the settings cache picks it up.
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

_tmp = tempfile.mkdtemp(prefix="bootapi-test-")
os.environ.setdefault("BOOTAPI_DATABASE_PATH", os.path.join(_tmp, "test.db"))
os.environ.setdefault("BOOTAPI_SECRET_KEY", "test-secret-not-for-production-use-0123456789")

from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    """A TestClient pointed at a fresh app + throwaway database."""
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register a fresh user and return headers with their bearer token."""
    import uuid

    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/auth/register", json={"email": email, "password": "correct-horse-123"}
    )
    assert response.status_code == 201
    response = client.post(
        "/auth/login", data={"username": email, "password": "correct-horse-123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
