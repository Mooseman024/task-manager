import copy
import pytest
from app import app
from services.users import USERS, list_users, get_notification_pref, set_notification_pref, get_user, create_user
from utils.errors import NotFoundError, ValidationError

@pytest.fixture(autouse=True)
def _reset_users():
    original = copy.deepcopy(USERS)
    yield
    USERS.clear()
    USERS.update(original)

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()

def test_get_notification_pref_default_none():
    assert get_notification_pref(1) is None

def test_get_notification_pref_unknown_user():
    with pytest.raises(NotFoundError):
        get_notification_pref(999)

def test_set_notification_pref_email():
    result = set_notification_pref(1, "email")
    assert result["notification_pref"] == "email"
    assert get_notification_pref(1) == "email"

def test_set_notification_pref_sms():
    result = set_notification_pref(1, "sms")
    assert result["notification_pref"] == "sms"
    assert get_notification_pref(1) == "sms"

def test_set_notification_pref_none_stores_none():
    set_notification_pref(1, "email")
    result = set_notification_pref(1, "none")
    assert result["notification_pref"] is None
    assert get_notification_pref(1) is None

def test_set_notification_pref_invalid_value():
    with pytest.raises(ValidationError):
        set_notification_pref(1, "carrier-pigeon")

def test_set_notification_pref_unknown_user():
    with pytest.raises(NotFoundError):
        set_notification_pref(999, "email")

def test_get_user_valid():
    user = get_user(1)
    assert user["id"] == 1
    assert user["name"] == "Alice"

def test_get_user_unknown_user():
    with pytest.raises(NotFoundError):
        get_user(999)

def test_create_user_valid():
    user = create_user("Carol", "carol@example.com")
    assert user["name"] == "Carol"
    assert user["email"] == "carol@example.com"
    assert user["notification_pref"] is None
    assert get_user(user["id"]) == user

def test_create_user_empty_name():
    with pytest.raises(ValidationError):
        create_user("", "carol@example.com")

def test_create_user_invalid_email():
    with pytest.raises(ValidationError):
        create_user("Carol", "not-an-email")

def test_list_users_includes_notification_pref():
    result = list_users()
    assert all("notification_pref" in u for u in result)

def test_get_users_route_includes_notification_pref(client):
    response = client.get("/api/users")
    assert response.status_code == 200
    body = response.get_json()
    assert all("notification_pref" in u for u in body)

def test_get_user_route_includes_notification_pref(client):
    response = client.get("/api/users/1")
    assert response.status_code == 200
    assert "notification_pref" in response.get_json()

def test_get_notifications_route_valid(client):
    response = client.get("/api/users/1/notifications")
    assert response.status_code == 200
    body = response.get_json()
    assert body["user_id"] == 1
    assert body["notification_pref"] is None

def test_get_notifications_route_unknown_user(client):
    response = client.get("/api/users/999/notifications")
    assert response.status_code == 404

def test_patch_notifications_route_valid(client):
    response = client.patch("/api/users/1/notifications", json={"notification_pref": "sms"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["notification_pref"] == "sms"

def test_patch_notifications_route_invalid_value(client):
    response = client.patch("/api/users/1/notifications", json={"notification_pref": "carrier-pigeon"})
    assert response.status_code == 422

def test_patch_notifications_route_unknown_user(client):
    response = client.patch("/api/users/999/notifications", json={"notification_pref": "email"})
    assert response.status_code == 404
