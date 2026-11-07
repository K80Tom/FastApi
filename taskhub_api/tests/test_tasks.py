from tests.conftest import auth, create_project, create_task, login, register


def test_complete_task_flow(client):
    register(client)
    token = login(client)
    project = create_project(client, token)
    task = create_task(client, token, project["id"])
    assert task["tags"][0]["name"] == "backend"

    response = client.get("/api/v1/tasks", headers=auth(token), params={"page": 1, "page_size": 10})
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 1

    response = client.patch(f"/api/v1/tasks/{task['id']}", headers=auth(token), json={"status": "doing"})
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "doing"

    response = client.post(f"/api/v1/tasks/{task['id']}/comments", headers=auth(token), json={"content": "Looks good"})
    assert response.status_code == 201
    response = client.get(f"/api/v1/tasks/{task['id']}/comments", headers=auth(token))
    assert response.json()["data"][0]["content"] == "Looks good"

    response = client.delete(f"/api/v1/tasks/{task['id']}", headers=auth(token))
    assert response.status_code == 204 and response.content == b""
    response = client.get(f"/api/v1/tasks/{task['id']}", headers=auth(token))
    assert response.status_code == 404


def test_non_member_and_viewer_permissions(client):
    owner_id = register(client)["id"]
    owner_token = login(client)
    project = create_project(client, owner_token)
    task = create_task(client, owner_token, project["id"])
    register(client, "bob")
    bob_token = login(client, "bob")

    response = client.get(f"/api/v1/tasks/{task['id']}", headers=auth(bob_token))
    assert response.status_code == 403
    response = client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers=auth(owner_token),
        json={"user_id": owner_id + 1, "role": "viewer"},
    )
    assert response.status_code == 201
    response = client.get(f"/api/v1/tasks/{task['id']}", headers=auth(bob_token))
    assert response.status_code == 200
    response = client.post(
        "/api/v1/tasks", headers=auth(bob_token), json={"project_id": project["id"], "title": "Not allowed"}
    )
    assert response.status_code == 403


def test_validation_errors_are_uniform(client):
    register(client)
    token = login(client)
    project = create_project(client, token)
    task = create_task(client, token, project["id"])
    response = client.post("/api/v1/tasks", headers=auth(token), json={"project_id": project["id"]})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert response.json()["request_id"]
    response = client.patch(f"/api/v1/tasks/{task['id']}", headers=auth(token), json={})
    assert response.status_code == 422
