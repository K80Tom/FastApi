from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def make_settings(tmp_path: Path, **overrides) -> Settings:
    values = {
        "database_url": f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        "jwt_secret_key": "test-secret-key-with-at-least-32-characters",
        "auto_create_tables": True,
        "upload_dir": tmp_path / "uploads",
        "max_upload_bytes": 1024,
    }
    values.update(overrides)
    return Settings(**values)


@pytest.fixture
def client(tmp_path):
    app = create_app(make_settings(tmp_path))
    with TestClient(app) as test_client:
        yield test_client


def register(client: TestClient, username="alice", email=None, password="correct-horse-123"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email or f"{username}@example.com",
            "username": username,
            "display_name": username.title(),
            "password": password,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def login(client: TestClient, username="alice", password="correct-horse-123") -> str:
    response = client.post("/api/v1/auth/token", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_project(client: TestClient, token: str, name="FastAPI Course") -> dict:
    response = client.post(
        "/api/v1/projects", headers=auth(token), json={"name": name, "description": "Course project"}
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def create_task(client: TestClient, token: str, project_id: int, title="Write tests") -> dict:
    response = client.post(
        "/api/v1/tasks",
        headers=auth(token),
        json={
            "project_id": project_id,
            "title": title,
            "description": "Verify the complete flow",
            "tags": [{"name": "backend", "color": "#2563eb"}],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]
