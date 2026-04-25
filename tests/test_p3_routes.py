from fastapi.testclient import TestClient


def test_p3_protected_routes_are_mounted(client: TestClient) -> None:
    protected_paths = [
        "/api/v1/reports/daily-sales",
        "/api/v1/leads/campaigns/summary",
        "/api/v1/automation/rules",
    ]

    for path in protected_paths:
        response = client.get(path)
        assert response.status_code == 401


def test_public_leads_route_is_mounted(client: TestClient) -> None:
    response = client.post(
        "/api/v1/public/leads",
        json={
            "branch_slug": "missing-branch",
            "full_name": "Public Lead",
            "phone": "9999999999",
            "utm_campaign": "spring",
        },
    )
    assert response.status_code == 404
