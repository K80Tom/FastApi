import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_http_client
from app.core.errors import UpstreamError
from app.main import create_app
from app.services.external_service import fetch_json_pair
from tests.conftest import login, make_settings, register


@pytest.mark.asyncio
async def test_external_requests_succeed():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"url": str(request.url)})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        first, second = await fetch_json_pair(client, "https://service.test/a", "https://service.test/b")
    assert first["url"].endswith("/a")
    assert second["url"].endswith("/b")


@pytest.mark.asyncio
async def test_external_failure_is_mapped_to_502():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"upstream": "unavailable"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(UpstreamError) as error:
            await fetch_json_pair(client, "https://service.test/a", "https://service.test/b")
    assert error.value.status_code == 502
    assert error.value.code == "UPSTREAM_ERROR"


def test_external_endpoint_uses_dependency_override(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"path": request.url.path})

    async def override_http_client():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as mock_client:
            yield mock_client

    app = create_app(make_settings(tmp_path))
    app.dependency_overrides[get_http_client] = override_http_client
    try:
        with TestClient(app) as client:
            register(client)
            token = login(client)
            response = client.get(
                "/api/v1/external/aggregate",
                params={
                    "url_a": "https://service.test/a",
                    "url_b": "https://service.test/b",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200, response.text
        assert response.json()["data"]["first"]["path"] == "/a"
        assert response.json()["data"]["second"]["path"] == "/b"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("failure_mode", ["timeout", "invalid_json", "non_object_json"])
@pytest.mark.asyncio
async def test_external_timeout_and_invalid_payloads_are_mapped(failure_mode):
    def handler(request: httpx.Request) -> httpx.Response:
        if failure_mode == "timeout":
            raise httpx.ReadTimeout("simulated timeout", request=request)
        if failure_mode == "invalid_json":
            return httpx.Response(200, content=b"not-json")
        return httpx.Response(200, json=["not", "an", "object"])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(UpstreamError):
            await fetch_json_pair(client, "https://service.test/a", "https://service.test/b")
