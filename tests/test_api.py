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
