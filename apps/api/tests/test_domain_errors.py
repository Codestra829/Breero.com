from fastapi.testclient import TestClient

from app.main import app


def test_health_live() -> None:
    response = TestClient(app).get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "live"}
    assert response.headers["x-request-id"]
