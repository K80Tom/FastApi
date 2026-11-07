from tests.conftest import auth, login, register


def test_register_login_and_me(client):
    user = register(client)
    assert user["username"] == "alice"
    assert "password" not in user and "password_hash" not in user
    token = login(client)
    response = client.get("/api/v1/users/me", headers=auth(token))
    assert response.status_code == 200
    assert response.json()["data"]["id"] == user["id"]


def test_duplicate_registration_returns_409(client):
    register(client)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "username": "alice",
            "display_name": "Alice",
            "password": "another-password-123",
        },
    )
    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"


def test_invalid_token_and_password_return_401(client):
    register(client)
    response = client.post("/api/v1/auth/token", data={"username": "alice", "password": "wrong-password"})
    assert response.status_code == 401
    response = client.get("/api/v1/users/me", headers=auth("not-a-valid-token"))
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
