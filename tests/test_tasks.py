import pytest
from services.tasks import create_task, get_task, process_order
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
