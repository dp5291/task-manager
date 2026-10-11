from services.users import get_user
from utils.errors import NotFoundError, ValidationError

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1, "priority": 3},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1, "priority": 3},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2, "priority": 3},
}

def process_order(task_id: int) -> dict:
    task = TASKS[task_id]
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

def create_task(title: str, user_id: int, priority: int = 3) -> dict:
    """Create a new task.

    Args:
        title: The task's title.
        user_id: The unique identifier for the user who owns the task.
        priority: Integer from 1 (urgent) to 5 (low). Defaults to 3.

    Returns:
        The newly created task record.

    Raises:
        ValidationError: If title is empty or priority is not an integer
            from 1 to 5.
        NotFoundError: If no user exists with the given ID.
    """
    if not title or not title.strip():
        raise ValidationError("title", "cannot be empty")
    _check_priority(priority)
    get_user(user_id)
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title,
                     "done": False, "user_id": user_id, "priority": priority}
    return TASKS[new_id]

def update_task(task_id: int, priority: int) -> dict:
    """Update a task's priority.

    Args:
        task_id: The unique identifier for the task.
        priority: New priority, an integer from 1 (urgent) to 5 (low).

    Returns:
        The updated task record.

    Raises:
        NotFoundError: If no task exists with the given ID.
        ValidationError: If priority is not an integer from 1 to 5.
    """
    task = get_task(task_id)
    _check_priority(priority)
    task["priority"] = priority
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

def list_tasks(priority: int | str | None = None) -> list[dict]:
    """Retrieve all tasks, optionally filtered by priority.

    Args:
        priority: Integer from 1 (urgent) to 5 (low), or its digit-string
            form (e.g. from a query string). None returns every task.

    Returns:
        A list of task records, empty if none match.

    Raises:
        ValidationError: If priority is not an integer from 1 to 5.
    """
    if priority is None:
        return list(TASKS.values())
    if isinstance(priority, str) and priority.isascii() and priority.isdigit():
        priority = int(priority)
    _check_priority(priority)
    return [task for task in TASKS.values() if task["priority"] == priority]
