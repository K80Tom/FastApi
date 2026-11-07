from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import make_settings


def test_request_id_and_cors_preflight(client):
    response = client.get("/health/live", headers={"X-Request-ID": "course-request-001"})
    assert response.headers["x-request-id"] == "course-request-001"
    assert "x-process-time-ms" in response.headers
    response = client.options(
        "/api/v1/users/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["x-request-id"]


def test_api_key_is_fail_closed(tmp_path):
    app = create_app(make_settings(tmp_path, api_key_enabled=True, api_key="test-api-key"))
    with TestClient(app) as client:
        assert client.get("/api/v1/service/info").status_code == 401
        assert client.get("/api/v1/service/info", headers={"X-API-Key": "wrong"}).status_code == 401
        response = client.get("/api/v1/service/info", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        assert response.json()["client"] == "api-key-client"


def test_api_key_enabled_without_key_fails_configuration(tmp_path):
    import pytest

    with pytest.raises(ValueError, match="API_KEY"):
        make_settings(tmp_path, api_key_enabled=True, api_key=None)
