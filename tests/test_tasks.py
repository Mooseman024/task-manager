import pytest
from app import app
from services.tasks import process_order, get_task, create_task, update_task, list_tasks
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

def test_update_task_valid_priority():
    created = create_task("Task to update", 1, priority=3)
    result = update_task(created["id"], {"priority": 5})
    assert result["priority"] == 5

def test_update_task_unknown_id():
    with pytest.raises(NotFoundError):
        update_task(999, {"priority": 2})

def test_update_task_invalid_priority():
    created = create_task("Task to update", 1, priority=3)
    with pytest.raises(ValidationError):
        update_task(created["id"], {"priority": 0})
    with pytest.raises(ValidationError):
        update_task(created["id"], {"priority": "high"})
    with pytest.raises(ValidationError):
        update_task(created["id"], {"priority": True})

def test_update_task_missing_priority():
    created = create_task("Task to update", 1, priority=3)
    with pytest.raises(ValidationError):
        update_task(created["id"], {})

def test_update_task_unknown_field():
    created = create_task("Task to update", 1, priority=3)
    with pytest.raises(ValidationError):
        update_task(created["id"], {"title": "new title"})
    with pytest.raises(ValidationError):
        update_task(created["id"], {"priority": 2, "extra": 1})

def test_list_tasks_no_filter():
    created = create_task("List task", 1, priority=2)
    result = list_tasks()
    assert created["id"] in [t["id"] for t in result]

def test_list_tasks_filter_matches_priority():
    created = create_task("Filtered task", 1, priority=2)
    result = list_tasks("2")
    assert created["id"] in [t["id"] for t in result]
    assert all(t["priority"] == 2 for t in result)

def test_list_tasks_filter_different_priority():
    created = create_task("Other filtered task", 1, priority=4)
    result = list_tasks("4")
    assert created["id"] in [t["id"] for t in result]
    assert all(t["priority"] == 4 for t in result)

def test_list_tasks_invalid_filter():
    with pytest.raises(ValidationError):
        list_tasks("abc")
    with pytest.raises(ValidationError):
        list_tasks("0")
    with pytest.raises(ValidationError):
        list_tasks("6")

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()

def test_patch_route_valid(client):
    created = create_task("Route task", 1, priority=3)
    response = client.patch(f"/api/tasks/{created['id']}", json={"priority": 4})
    assert response.status_code == 200
    assert response.get_json()["priority"] == 4

def test_patch_route_unknown_field(client):
    created = create_task("Route task", 1, priority=3)
    response = client.patch(f"/api/tasks/{created['id']}", json={"title": "x"})
    assert response.status_code == 422

def test_patch_route_missing_priority(client):
    created = create_task("Route task", 1, priority=3)
    response = client.patch(f"/api/tasks/{created['id']}", json={})
    assert response.status_code == 422

def test_patch_route_unknown_task(client):
    response = client.patch("/api/tasks/999", json={"priority": 2})
    assert response.status_code == 404

def test_list_tasks_route_invalid_priority(client):
    response = client.get("/api/tasks?priority=abc")
    assert response.status_code == 422
