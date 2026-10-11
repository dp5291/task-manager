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
