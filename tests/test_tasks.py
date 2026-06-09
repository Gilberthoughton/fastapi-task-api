"""Tests for task CRUD and ownership isolation."""


def _other_user_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "password": "password123"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "other@example.com", "password": "password123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_task(client, auth_headers):
    resp = client.post(
        "/api/v1/tasks",
        json={"title": "Write README", "description": "Cover setup"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Write README"
    assert body["completed"] is False
    assert "owner_id" in body


def test_create_task_requires_auth(client):
    resp = client.post("/api/v1/tasks", json={"title": "x"})
    assert resp.status_code == 401


def test_create_task_validation_error(client, auth_headers):
    resp = client.post("/api/v1/tasks", json={"title": ""}, headers=auth_headers)
    assert resp.status_code == 422


def test_list_tasks(client, auth_headers):
    for i in range(3):
        client.post(
            "/api/v1/tasks",
            json={"title": f"Task {i}"},
            headers=auth_headers,
        )
    resp = client.get("/api/v1/tasks", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_get_single_task(client, auth_headers):
    created = client.post(
        "/api/v1/tasks", json={"title": "Find me"}, headers=auth_headers
    ).json()
    resp = client.get(f"/api/v1/tasks/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_update_task(client, auth_headers):
    created = client.post(
        "/api/v1/tasks", json={"title": "Old"}, headers=auth_headers
    ).json()
    resp = client.patch(
        f"/api/v1/tasks/{created['id']}",
        json={"title": "New", "completed": True},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New"
    assert resp.json()["completed"] is True


def test_delete_task(client, auth_headers):
    created = client.post(
        "/api/v1/tasks", json={"title": "Temp"}, headers=auth_headers
    ).json()
    resp = client.delete(f"/api/v1/tasks/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert (
        client.get(f"/api/v1/tasks/{created['id']}", headers=auth_headers).status_code
        == 404
    )


def test_user_cannot_access_others_task(client, auth_headers):
    """Ownership isolation: a second user gets 404 for the first user's task."""
    created = client.post(
        "/api/v1/tasks", json={"title": "Private"}, headers=auth_headers
    ).json()

    other = _other_user_headers(client)
    assert (
        client.get(f"/api/v1/tasks/{created['id']}", headers=other).status_code == 404
    )
    assert (
        client.delete(f"/api/v1/tasks/{created['id']}", headers=other).status_code
        == 404
    )
