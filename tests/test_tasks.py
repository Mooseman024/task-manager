import pytest
from services.tasks import process_order, get_task, create_task
from utils.errors import ValidationError

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

def test_create_task_default_priority():
    result = create_task("Walk dog", 1)
    assert result["priority"] == 3

def test_create_task_explicit_priority():
    result = create_task("Fix bug", 1, priority=1)
    assert result["priority"] == 1

def test_create_task_invalid_priority_out_of_range():
    with pytest.raises(ValidationError):
        create_task("Bad task", 1, priority=0)
    with pytest.raises(ValidationError):
        create_task("Bad task", 1, priority=6)

def test_create_task_invalid_priority_non_integer():
    with pytest.raises(ValidationError):
        create_task("Bad task", 1, priority="high")

def test_create_task_invalid_priority_bool():
    with pytest.raises(ValidationError):
        create_task("Bad task", 1, priority=True)
    with pytest.raises(ValidationError):
        create_task("Bad task", 1, priority=False)
