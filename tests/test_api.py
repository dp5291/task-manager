import pytest
from app import app
from services.tasks import process_order

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

def test_list_tasks_route_sort_by_priority():
    client = app.test_client()
    urgent_id = None
    for priority in [5, 1, 2]:
        task = client.post("/api/tasks", json={"title": "Sort me", "user_id": 1, "priority": priority}).get_json()
        if priority == 1:
            urgent_id = task["id"]
    response = client.get("/api/tasks?sort=priority")
    assert response.status_code == 200
    keys = [(task["priority"], task["id"]) for task in response.get_json()]
    assert keys == sorted(keys)
    ids = [task_id for _, task_id in keys]
    assert ids.index(urgent_id) < ids.index(1)

def test_list_tasks_route_sort_with_priority_filter():
    client = app.test_client()
    for _ in range(2):
        client.post("/api/tasks", json={"title": "Filter sort", "user_id": 1, "priority": 2})
    response = client.get("/api/tasks?priority=2&sort=priority")
    assert response.status_code == 200
    result = response.get_json()
    assert len(result) >= 2
    assert all(task["priority"] == 2 for task in result)
    ids = [task["id"] for task in result]
    assert all(a < b for a, b in zip(ids, ids[1:]))

@pytest.mark.parametrize("sort", ["bogus", "id", ""])
def test_list_tasks_route_invalid_sort_returns_422(sort):
    response = app.test_client().get(f"/api/tasks?sort={sort}")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid sort: must be priority"}

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

BAD_BODIES = [
    {},
    {"data": "not json", "content_type": "text/plain"},
    {"data": "{", "content_type": "application/json"},
    {"json": [1]},
]

@pytest.mark.parametrize("kwargs", BAD_BODIES)
def test_create_task_route_bad_body(kwargs):
    response = app.test_client().post("/api/tasks", **kwargs)
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid body: must be a JSON object"}

@pytest.mark.parametrize("kwargs", BAD_BODIES)
def test_update_task_route_bad_body(kwargs):
    client = app.test_client()
    task_id = client.post("/api/tasks", json={"title": "Bad body", "user_id": 1}).get_json()["id"]
    response = client.patch(f"/api/tasks/{task_id}", **kwargs)
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid body: must be a JSON object"}

@pytest.mark.parametrize("body", [{"user_id": 1}, {"title": None, "user_id": 1}, {"title": 123, "user_id": 1}])
def test_create_task_route_non_string_title(body):
    response = app.test_client().post("/api/tasks", json=body)
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid title: must be a string"}

@pytest.mark.parametrize("title", ["", "   "])
def test_create_task_route_empty_title(title):
    response = app.test_client().post("/api/tasks", json={"title": title, "user_id": 1})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid title: cannot be empty"}

@pytest.mark.parametrize("body", [
    {"title": "No user"},
    {"title": "Bad user", "user_id": "1"},
    {"title": "Bad user", "user_id": 1.5},
    {"title": "Bad user", "user_id": None},
    {"title": "Bad user", "user_id": True},
])
def test_create_task_route_invalid_user_id(body):
    response = app.test_client().post("/api/tasks", json=body)
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid user_id: must be an integer"}

DUE_DATE_ERROR = {"error": "Invalid due_date: must be a date in YYYY-MM-DD format"}
INVALID_DUE_DATES = ["2026-13-01", "2026-02-30", "20261201", "12/01/2026", "", 20261201, True]

def test_create_task_route_with_due_date():
    client = app.test_client()
    response = client.post("/api/tasks", json={"title": "Due", "user_id": 1, "due_date": "2026-12-01"})
    assert response.status_code == 201
    assert response.get_json()["due_date"] == "2026-12-01"
    task_id = response.get_json()["id"]
    assert client.get(f"/api/tasks/{task_id}").get_json()["due_date"] == "2026-12-01"

@pytest.mark.parametrize("due_date", INVALID_DUE_DATES)
def test_create_task_route_invalid_due_date(due_date):
    response = app.test_client().post("/api/tasks", json={"title": "Bad", "user_id": 1, "due_date": due_date})
    assert response.status_code == 422
    assert response.get_json() == DUE_DATE_ERROR

def test_update_task_route_due_date_only():
    client = app.test_client()
    task_id = client.post("/api/tasks", json={"title": "Set due", "user_id": 1, "priority": 2}).get_json()["id"]
    response = client.patch(f"/api/tasks/{task_id}", json={"due_date": "2026-12-01"})
    assert response.status_code == 200
    assert response.get_json()["due_date"] == "2026-12-01"
    assert response.get_json()["priority"] == 2

def test_update_task_route_clear_due_date():
    client = app.test_client()
    task_id = client.post("/api/tasks", json={"title": "Clear due", "user_id": 1, "due_date": "2026-12-01"}).get_json()["id"]
    response = client.patch(f"/api/tasks/{task_id}", json={"due_date": None})
    assert response.status_code == 200
    assert response.get_json()["due_date"] is None

@pytest.mark.parametrize("due_date", INVALID_DUE_DATES)
def test_update_task_route_invalid_due_date(due_date):
    client = app.test_client()
    task_id = client.post("/api/tasks", json={"title": "Bad due", "user_id": 1}).get_json()["id"]
    response = client.patch(f"/api/tasks/{task_id}", json={"due_date": due_date})
    assert response.status_code == 422
    assert response.get_json() == DUE_DATE_ERROR

def test_update_task_route_empty_object():
    client = app.test_client()
    task_id = client.post("/api/tasks", json={"title": "Empty patch", "user_id": 1}).get_json()["id"]
    response = client.patch(f"/api/tasks/{task_id}", json={})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid body: must include priority or due_date"}

def test_list_tasks_route_overdue():
    client = app.test_client()
    late_id = client.post("/api/tasks", json={"title": "Late", "user_id": 1, "due_date": "2000-01-01"}).get_json()["id"]
    done_id = client.post("/api/tasks", json={"title": "Late done", "user_id": 1, "due_date": "2000-01-01"}).get_json()["id"]
    process_order(done_id)
    client.post("/api/tasks", json={"title": "Future", "user_id": 1, "due_date": "2999-12-31"})
    response = client.get("/api/tasks?overdue=true")
    assert response.status_code == 200
    assert [task["id"] for task in response.get_json()] == [late_id]

def test_list_tasks_route_invalid_overdue():
    response = app.test_client().get("/api/tasks?overdue=bogus")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid overdue: must be true or false"}
