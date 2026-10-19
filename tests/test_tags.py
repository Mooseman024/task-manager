import copy
import pytest
from app import app
from services.tags import TAGS

@pytest.fixture(autouse=True)
def _reset_tags():
    original = copy.deepcopy(TAGS)
    yield
    TAGS.clear()
    TAGS.update(original)

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()

def test_create_tag_route_valid(client):
    response = client.post("/api/tags", json={"name": "urgent"})
    assert response.status_code == 201
    assert response.get_json()["name"] == "urgent"

def test_create_tag_route_missing_field(client):
    response = client.post("/api/tags", json={})
    assert response.status_code == 422

def test_create_tag_route_null_body(client):
    response = client.post("/api/tags", data="null", content_type="application/json")
    assert response.status_code == 422
