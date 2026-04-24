"""Authentication endpoint tests."""
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.enums import RoleEnum
from app.core.security import hash_password
from app.models import Branch, Organization, Staff, User


def test_login_success(client: TestClient, session: Session) -> None:
    """Test successful login with valid credentials."""
    # Setup organization
    org = Organization(name="Test Gym", slug="test-gym", owner_email="owner@test.com")
    session.add(org)
    session.commit()
    session.refresh(org)

    # Setup branch
    branch = Branch(organization_id=org.id, name="Main Branch")
    session.add(branch)
    session.commit()
    session.refresh(branch)

    # Setup user
    user = User(
        email="staff@test.com",
        hashed_password=hash_password("password123"),
        full_name="Test Staff",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Setup staff
    staff = Staff(
        user_id=user.id,
        organization_id=org.id,
        branch_id=branch.id,
        role=RoleEnum.FRONT_DESK,
        joined_at=date.today(),
    )
    session.add(staff)
    session.commit()

    # Test login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "staff@test.com", "password": "password123"},
    )
    assert response.status_code == 200
    data: dict[str, Any] = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient) -> None:
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_missing_fields(client: TestClient) -> None:
    """Test login with missing required fields."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com"},
    )
    assert response.status_code == 422


def test_login_empty_body(client: TestClient) -> None:
    """Test login with empty request body."""
    response = client.post("/api/v1/auth/login", json={})
    assert response.status_code == 422
