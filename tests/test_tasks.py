import pytest
from services.tasks import archive_task, create_task, get_task, get_tasks_for_user, list_tasks, process_order, update_task
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
    with pytest.raises(NotFoundError):
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

def test_list_tasks_no_filter_returns_all():
    ids = [task["id"] for task in list_tasks()]
    assert 1 in ids and 2 in ids and 3 in ids

def test_list_tasks_filter_by_priority():
    created = create_task("Priority two", 1, priority=2)
    result = list_tasks(2)
    ids = [task["id"] for task in result]
    assert created["id"] in ids
    assert 1 not in ids
    assert all(task["priority"] == 2 for task in result)

def test_list_tasks_filter_by_priority_string():
    created = create_task("Priority four", 1, priority=4)
    result = list_tasks("4")
    assert created["id"] in [task["id"] for task in result]
    assert all(task["priority"] == 4 for task in result)

@pytest.mark.parametrize("priority", [0, 6, "abc", "", "-1", "2.5", True])
def test_list_tasks_invalid_priority(priority):
    with pytest.raises(ValidationError):
        list_tasks(priority)

def test_update_task_priority():
    created = create_task("Reprioritize me", 1)
    result = update_task(created["id"], 1)
    assert result["priority"] == 1
    assert get_task(created["id"])["priority"] == 1

def test_update_task_unknown_task():
    with pytest.raises(NotFoundError):
        update_task(999, 2)

@pytest.mark.parametrize("priority", [0, 6, -1, "high", 2.5, None, True])
def test_update_task_invalid_priority(priority):
    created = create_task("Bad update", 1)
    with pytest.raises(ValidationError):
        update_task(created["id"], priority)

@pytest.mark.parametrize("title", [None, 123])
def test_create_task_non_string_title(title):
    with pytest.raises(ValidationError):
        create_task(title, 1)

@pytest.mark.parametrize("user_id", ["1", 1.5, None, True])
def test_create_task_invalid_user_id(user_id):
    with pytest.raises(ValidationError):
        create_task("Bad user", user_id)

def test_process_order_unknown_task_raises_not_found():
    with pytest.raises(NotFoundError):
        process_order(999)

def test_archive_task_sets_archived():
    assert archive_task(1)["archived"] is True
    assert get_task(1)["archived"] is True

def test_archive_task_unknown_id():
    with pytest.raises(NotFoundError):
        archive_task(999)

def test_create_task_starts_unarchived():
    assert create_task("New", 1)["archived"] is False

def test_list_tasks_hides_archived_by_default():
    archive_task(2)
    ids = [task["id"] for task in list_tasks()]
    assert 2 not in ids
    assert 1 in ids and 3 in ids

def test_list_tasks_include_archived_true():
    archive_task(2)
    ids = [task["id"] for task in list_tasks(include_archived="true")]
    assert 2 in ids

def test_list_tasks_invalid_include_archived():
    with pytest.raises(ValidationError):
        list_tasks(include_archived="yes")

@pytest.mark.parametrize("include_archived", [1, 0])
def test_list_tasks_include_archived_rejects_int(include_archived):
    with pytest.raises(ValidationError):
        list_tasks(include_archived=include_archived)

def test_list_tasks_priority_and_archive_filters_combined():
    created = create_task("Combo", 1, 2)
    archive_task(created["id"])
    hidden = list_tasks(2)
    shown = list_tasks(2, include_archived="true")
    assert created["id"] not in [task["id"] for task in hidden]
    assert created["id"] in [task["id"] for task in shown]
    assert all(task["priority"] == 2 for task in hidden + shown)
