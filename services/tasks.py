from utils.errors import NotFoundError, ValidationError

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1, "priority": 3},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1, "priority": 3},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2, "priority": 3},
}

def process_order(task_id: int) -> dict:
    """Mark a task as done.

    Args:
        task_id: The ID of the task to mark as done.

    Returns:
        The updated task record.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
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

def _validate_priority(priority: int) -> None:
    """Validate that a priority value is an integer between 1 and 5.

    Args:
        priority: The priority value to validate.

    Raises:
        ValidationError: If priority is not an integer between 1 and 5.
    """
    if isinstance(priority, bool) or not isinstance(priority, int) or not (1 <= priority <= 5):
        raise ValidationError("priority", "must be an integer between 1 and 5")

def list_tasks(priority: str | None = None) -> list[dict]:
    """List all tasks, optionally filtered by priority.

    Args:
        priority: If given, the raw priority filter value (expected to be an
            integer 1-5 as a string). None means no filtering.

    Returns:
        A list of matching task records.

    Raises:
        ValidationError: If priority is given and is not an integer between 1 and 5.
    """
    if priority is None:
        return list(TASKS.values())
    try:
        priority_int = int(priority)
    except ValueError:
        raise ValidationError("priority", "must be an integer between 1 and 5")
    _validate_priority(priority_int)
    return [t for t in TASKS.values() if t["priority"] == priority_int]

def create_task(title: str, user_id: int, priority: int = 3) -> dict:
    """Create a new task.

    Args:
        title: The task's title.
        user_id: The ID of the user the task belongs to.
        priority: The task's priority, 1 (urgent) to 5 (low). Defaults to 3.

    Returns:
        The newly created task record.

    Raises:
        ValidationError: If priority is not an integer between 1 and 5.
    """
    _validate_priority(priority)
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title,
                     "done": False, "user_id": user_id, "priority": priority}
    return TASKS[new_id]

def update_task(task_id: int, data: dict) -> dict:
    """Update a task's priority.

    Args:
        task_id: The ID of the task to update.
        data: The update payload. Must contain only the "priority" field.

    Returns:
        The updated task record.

    Raises:
        NotFoundError: If no task exists with the given ID.
        ValidationError: If data contains an unknown field, is missing
            "priority", or "priority" is not an integer between 1 and 5.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    for field in data:
        if field != "priority":
            raise ValidationError(field, "unknown field")
    if "priority" not in data:
        raise ValidationError("priority", "is required")
    _validate_priority(data["priority"])
    task = TASKS[task_id]
    task["priority"] = data["priority"]
    return task
