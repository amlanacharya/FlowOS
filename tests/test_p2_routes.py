from fastapi.testclient import TestClient


def test_p2_routes_are_mounted(client: TestClient) -> None:
    """P2 routers should be reachable and protected by auth."""
    protected_paths = [
        "/api/v1/workouts/member-id",
        "/api/v1/feedback/summary",
        "/api/v1/trainer/today",
    ]

    for path in protected_paths:
        response = client.get(path)
        assert response.status_code == 401
