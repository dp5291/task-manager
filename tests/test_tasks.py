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
