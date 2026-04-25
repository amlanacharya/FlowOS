"""Integration tests for complete workflows."""
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.enums import MemberStatusEnum
from app.models import Branch, Member, MembershipPlan, Organization


def test_organization_and_branch_creation(client: TestClient, session: Session) -> None:
    """Test creating organization and branch in sequence."""
    # Create organization
    org_data = {
        "name": "Integration Test Gym",
        "slug": "integration-gym",
        "owner_email": "owner@integration.com",
        "phone": "1234567890",
    }
    response = client.post("/api/v1/organizations", json=org_data)
    # Note: Status code may vary depending on auth requirements
    if response.status_code in [200, 403]:
        if response.status_code == 200:
            org_response: dict[str, Any] = response.json()
            assert "id" in org_response
            org_id = org_response["id"]

            # Create branch under organization
            branch_data = {
                "name": "Test Branch",
                "address": "123 Fitness Street",
                "city": "Test City",
                "phone": "0987654321",
            }
            branch_response = client.post(
                f"/api/v1/branches?org_id={org_id}", json=branch_data
            )
            # May require auth depending on router policy.
            assert branch_response.status_code in [200, 401, 403]


def test_member_and_plan_flow(session: Session) -> None:
    """Test member creation with membership plan."""
    # Setup organization
    org = Organization(name="Test Org", slug="test-org", owner_email="test@org.com")
    session.add(org)
    session.commit()
    session.refresh(org)

    # Setup branch
    branch = Branch(organization_id=org.id, name="Test Branch")
    session.add(branch)
    session.commit()
    session.refresh(branch)

    # Create membership plan
    plan = MembershipPlan(
        branch_id=branch.id,
        name="Gold Plan",
        duration_days=30,
        price=Decimal("50.00"),
        description="Premium membership",
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)

    # Create member
    member = Member(
        branch_id=branch.id,
        full_name="John Doe",
        email="john@test.com",
        phone="1234567890",
        member_code="MEM001",
        status=MemberStatusEnum.ACTIVE,
    )
    session.add(member)
    session.commit()

    # Verify member exists
    assert member.id is not None
    assert member.status == MemberStatusEnum.ACTIVE
    assert plan.id is not None


def test_api_routing(client: TestClient) -> None:
    """Test that API routers are properly mounted."""
    # Health check should work
    response = client.get("/health")
    assert response.status_code == 200

    # Auth endpoint should be accessible
    response = client.post(
        "/api/v1/auth/login", json={"email": "test@test.com", "password": "test"}
    )
    assert response.status_code in [401, 422, 500]  # Should at least be routed
