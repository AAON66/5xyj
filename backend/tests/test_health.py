from fastapi.testclient import TestClient

from backend.app.main import app


def test_healthcheck_returns_wrapped_success_payload() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["status"] == "ok"
