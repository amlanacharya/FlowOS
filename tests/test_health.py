"""Basic health check endpoint tests."""
from typing import Any

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Test health check endpoint returns correct response."""
    response = client.get("/health")
    assert response.status_code == 200
    data: dict[str, Any] = response.json()
    assert data == {"status": "ok"}


def test_health_endpoint_content_type(client: TestClient) -> None:
    """Test health endpoint returns JSON content type."""
    response = client.get("/health")
    assert response.headers["content-type"].startswith("application/json")
