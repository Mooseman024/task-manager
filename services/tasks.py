from utils.errors import ValidationError

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1, "priority": 3},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1, "priority": 3},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2, "priority": 3},
}

def process_order(task_id: int) -> dict:
    try:
        task = TASKS[task_id]
    except KeyError:
        raise ValueError(f"Task {task_id} does not exist")
    task["done"] = True
    return task

def get_task(task_id: int) -> dict:
    return TASKS[task_id]

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
    if isinstance(priority, bool) or not isinstance(priority, int) or not (1 <= priority <= 5):
        raise ValidationError("priority", "must be an integer between 1 and 5")
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title,
                     "done": False, "user_id": user_id, "priority": priority}
    return TASKS[new_id]
