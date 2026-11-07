from tests.conftest import auth, create_project, login, register


def test_sse_stream(client):
    register(client)
    token = login(client)
    response = client.get("/api/v1/events/stream?limit=2", headers=auth(token))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "id: 2" in response.text
    assert "event: heartbeat" in response.text


def test_websocket_authentication_and_ping(client):
    register(client)
    token = login(client)
    project = create_project(client, token)
    with client.websocket_connect(f"/api/v1/ws/projects/{project['id']}") as websocket:
        websocket.send_json({"type": "authenticate", "token": token})
        assert websocket.receive_json()["type"] == "ready"
        websocket.send_json({"type": "ping"})
        assert websocket.receive_json() == {"type": "pong"}
