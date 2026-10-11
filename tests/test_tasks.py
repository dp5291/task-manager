import pytest
from services.tasks import create_task, get_task, get_tasks_for_user, process_order
from utils.errors import NotFoundError, ValidationError

def test_process_order_valid():
    result = process_order(1)
    assert result["done"] is True

def test_process_order_invalid():
    with pytest.raises(Exception):
        process_order(999)

def test_get_task_valid():
    result = get_task(2)
    assert result["title"] == "Write report"

def test_get_task_invalid():
    with pytest.raises(Exception):
        get_task(999)

def test_create_task_empty_title():
    
    with pytest.raises(ValidationError):
        create_task("   ", 1)

def test_create_task_unknown_user():
    
    with pytest.raises(NotFoundError):
        create_task("New task", 999)

def test_get_tasks_for_user_valid():
    result = get_tasks_for_user(1)
    ids = [task["id"] for task in result]
    assert 1 in ids and 2 in ids
    assert 3 not in ids
    assert all(task["user_id"] == 1 for task in result)

def test_get_tasks_for_user_unknown_user():
    with pytest.raises(NotFoundError):
        get_tasks_for_user(999)

def test_seed_tasks_have_priority():
    for task_id in (1, 2, 3):
        priority = get_task(task_id)["priority"]
        assert isinstance(priority, int) and 1 <= priority <= 5

def test_create_task_default_priority():
    result = create_task("Default priority", 1)
    assert result["priority"] == 3

def test_create_task_with_priority():
    assert create_task("Urgent task", 1, priority=1)["priority"] == 1
    assert create_task("Low task", 1, priority=5)["priority"] == 5

@pytest.mark.parametrize("priority", [0, 6, -1, "high", 2.5, None, True])
def test_create_task_invalid_priority(priority):
    with pytest.raises(ValidationError):
        create_task("Bad priority", 1, priority=priority)
