import re
from datetime import date

from services.users import get_user
from utils.errors import NotFoundError, ValidationError

_UNSET = object()

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1, "priority": 3},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1, "priority": 3},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2, "priority": 3},
}

def process_order(task_id: int) -> dict:
    """Mark a task as done.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The updated task record.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    task = get_task(task_id)
    task["done"] = True
    return task

def get_task(task_id: int) -> dict:
    """Retrieve a task by ID.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    return TASKS[task_id]

def _check_priority(priority: int) -> None:
    """Validate a task priority.

    Args:
        priority: The value to check; must be an integer from 1 to 5.

    Raises:
        ValidationError: If priority is a bool, not an int, or outside 1-5.
    """
    if isinstance(priority, bool) or not isinstance(priority, int) or not 1 <= priority <= 5:
        raise ValidationError("priority", "must be an integer from 1 to 5")

def _check_due_date(due_date: object) -> None:
    """Validate a task due date.

    Args:
        due_date: The value to check; must be a real calendar date as a
            "YYYY-MM-DD" string.

    Raises:
        ValidationError: If due_date is not a string in YYYY-MM-DD format
            or is not a real date.
    """
    if not isinstance(due_date, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", due_date):
        raise ValidationError("due_date", "must be a date in YYYY-MM-DD format")
    try:
        date.fromisoformat(due_date)
    except ValueError:
        raise ValidationError("due_date", "must be a date in YYYY-MM-DD format") from None

def create_task(title: str, user_id: int, priority: int = 3, due_date: str | None = None) -> dict:
    """Create a new task.

    Args:
        title: The task's title.
        user_id: The unique identifier for the user who owns the task.
        priority: Integer from 1 (urgent) to 5 (low). Defaults to 3.
        due_date: Optional due date as a "YYYY-MM-DD" string. Defaults to None.

    Returns:
        The newly created task record.

    Raises:
        ValidationError: If title is not a string or is empty, priority is
            not an integer from 1 to 5, user_id is not an integer, or
            due_date is not None or a YYYY-MM-DD date.
        NotFoundError: If no user exists with the given ID.
    """
    if not isinstance(title, str):
        raise ValidationError("title", "must be a string")
    if not title or not title.strip():
        raise ValidationError("title", "cannot be empty")
    _check_priority(priority)
    if due_date is not None:
        _check_due_date(due_date)
    if isinstance(user_id, bool) or not isinstance(user_id, int):
        raise ValidationError("user_id", "must be an integer")
    get_user(user_id)
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title, "done": False,
                     "user_id": user_id, "priority": priority, "due_date": due_date}
    return TASKS[new_id]

def update_task(task_id: int, priority: int | object = _UNSET,
                due_date: str | None | object = _UNSET) -> dict:
    """Update a task's priority and/or due date.

    Args:
        task_id: The unique identifier for the task.
        priority: New priority, an integer from 1 (urgent) to 5 (low).
            Omit to leave it unchanged.
        due_date: New due date as a "YYYY-MM-DD" string, or None to clear
            it. Omit to leave it unchanged.

    Returns:
        The updated task record.

    Raises:
        NotFoundError: If no task exists with the given ID.
        ValidationError: If neither field is given, priority is not an
            integer from 1 to 5, or due_date is not None or a YYYY-MM-DD date.
    """
    task = get_task(task_id)
    if priority is _UNSET and due_date is _UNSET:
        raise ValidationError("body", "must include priority or due_date")
    if priority is not _UNSET:
        _check_priority(priority)
    if due_date is not _UNSET and due_date is not None:
        _check_due_date(due_date)
    if priority is not _UNSET:
        task["priority"] = priority
    if due_date is not _UNSET:
        task["due_date"] = due_date
    return task

def get_tasks_for_user(user_id: int) -> list[dict]:
    """Retrieve all tasks owned by a user.

    Args:
        user_id: The unique identifier for the user who owns the tasks.

    Returns:
        A list of the user's task records, empty if they have none.

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    get_user(user_id)
    return [task for task in TASKS.values() if task["user_id"] == user_id]

def list_tasks(priority: int | str | None = None, overdue: bool | str | None = None,
               today: date | None = None) -> list[dict]:
    """Retrieve all tasks, optionally filtered by priority and overdue status.

    Args:
        priority: Integer from 1 (urgent) to 5 (low), or its digit-string
            form (e.g. from a query string). None applies no priority filter.
        overdue: True or "true" keeps only tasks that are not done and whose
            due_date is before today. None, False or "false" applies no filter.
        today: The date to compare due dates against. Defaults to date.today().

    Returns:
        A list of task records, empty if none match.

    Raises:
        ValidationError: If priority is not an integer from 1 to 5, or
            overdue is not true or false.
    """
    if overdue is None or overdue is False or overdue == "false":
        overdue = False
    elif overdue is True or overdue == "true":
        overdue = True
    else:
        raise ValidationError("overdue", "must be true or false")
    tasks = list(TASKS.values())
    if priority is not None:
        if isinstance(priority, str) and priority.isascii() and priority.isdigit():
            priority = int(priority)
        _check_priority(priority)
        tasks = [task for task in tasks if task["priority"] == priority]
    if overdue:
        if today is None:
            today = date.today()
        tasks = [task for task in tasks
                 if task.get("due_date") is not None
                 and date.fromisoformat(task["due_date"]) < today
                 and not task["done"]]
    return tasks
