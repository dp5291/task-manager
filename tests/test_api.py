import pytest
from app import app

def test_list_tasks_route_invalid_priority_returns_422():
    response = app.test_client().get("/api/tasks?priority=abc")
    assert response.status_code == 422
    assert "error" in response.get_json()

def test_list_tasks_route_filters_by_priority():
    response = app.test_client().get("/api/tasks?priority=3")
    assert response.status_code == 200
    result = response.get_json()
    assert result
    assert all(task["priority"] == 3 for task in result)

def test_update_task_route_valid():
    client = app.test_client()
    task_id = client.post("/api/tasks", json={"title": "Patch me", "user_id": 1}).get_json()["id"]
    response = client.patch(f"/api/tasks/{task_id}", json={"priority": 5})
    assert response.status_code == 200
    assert response.get_json()["priority"] == 5

def test_update_task_route_unknown_task():
    response = app.test_client().patch("/api/tasks/999", json={"priority": 2})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}

def test_update_task_route_invalid_priority():
    client = app.test_client()
    task_id = client.post("/api/tasks", json={"title": "Bad patch", "user_id": 1}).get_json()["id"]
    response = client.patch(f"/api/tasks/{task_id}", json={"priority": 9})
    assert response.status_code == 422
    assert "error" in response.get_json()

def test_create_task_route_with_priority():
    response = app.test_client().post("/api/tasks", json={"title": "Urgent", "user_id": 1, "priority": 1})
    assert response.status_code == 201
    assert response.get_json()["priority"] == 1

def test_create_task_route_default_priority():
    response = app.test_client().post("/api/tasks", json={"title": "Default", "user_id": 1})
    assert response.status_code == 201
    assert response.get_json()["priority"] == 3

def test_get_task_route_shows_priority():
    client = app.test_client()
    task_id = client.post("/api/tasks", json={"title": "Get me", "user_id": 1, "priority": 2}).get_json()["id"]
    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    assert response.get_json()["priority"] == 2

def test_patch_task_route_shows_priority_after_create():
    client = app.test_client()
    task_id = client.post("/api/tasks", json={"title": "Repatch", "user_id": 1, "priority": 4}).get_json()["id"]
    response = client.patch(f"/api/tasks/{task_id}", json={"priority": 1})
    assert response.status_code == 200
    assert response.get_json()["priority"] == 1
    assert client.get(f"/api/tasks/{task_id}").get_json()["priority"] == 1

@pytest.mark.parametrize("priority", [9, 0, "high", None])
def test_create_task_route_invalid_priority(priority):
    response = app.test_client().post("/api/tasks", json={"title": "Bad", "user_id": 1, "priority": priority})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid priority: must be an integer from 1 to 5"}
