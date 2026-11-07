from tests.conftest import auth, create_project, create_task, login, register


def test_upload_and_download_with_safe_storage_name(client):
    register(client)
    token = login(client)
    project = create_project(client, token)
    task = create_task(client, token, project["id"])
    response = client.post(
        f"/api/v1/tasks/{task['id']}/attachments",
        headers=auth(token),
        files={"upload": ("../../notes.txt", b"hello taskhub", "text/plain")},
    )
    assert response.status_code == 201, response.text
    attachment = response.json()["data"]
    assert attachment["original_name"] == "notes.txt"
    response = client.get(f"/api/v1/attachments/{attachment['id']}", headers=auth(token))
    assert response.status_code == 200
    assert response.content == b"hello taskhub"


def test_file_size_and_signature_validation(client):
    register(client)
    token = login(client)
    project = create_project(client, token)
    task = create_task(client, token, project["id"])
    response = client.post(
        f"/api/v1/tasks/{task['id']}/attachments",
        headers=auth(token),
        files={"upload": ("large.txt", b"x" * 1025, "text/plain")},
    )
    assert response.status_code == 413
    response = client.post(
        f"/api/v1/tasks/{task['id']}/attachments",
        headers=auth(token),
        files={"upload": ("fake.png", b"not-a-png", "image/png")},
    )
    assert response.status_code == 400
