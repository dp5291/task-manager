import copy

import pytest
from app import app
from services.tags import TAGS, create_tag
from utils.errors import ValidationError


@pytest.fixture(autouse=True)
def restore_tags():
    snapshot = copy.deepcopy(TAGS)
    yield
    TAGS.clear()
    TAGS.update(snapshot)


@pytest.fixture
def client():
    return app.test_client()


# Service tests

def test_create_tag_returns_record():
    tag = create_tag("  urgent  ")
    assert tag == {"id": tag["id"], "name": "urgent"}
    assert TAGS[tag["id"]] == tag

def test_create_tag_non_string_name_raises_validation_error():
    with pytest.raises(ValidationError):
        create_tag(123)

def test_create_tag_empty_name_raises_validation_error():
    with pytest.raises(ValidationError):
        create_tag("   ")

def test_create_tag_duplicate_name_raises_validation_error():
    create_tag("work")
    with pytest.raises(ValidationError):
        create_tag("WORK")


# Route tests

def test_create_tag_route_returns_201(client):
    response = client.post("/api/tags", json={"name": "home"})
    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "home"
    assert isinstance(body["id"], int)
    assert TAGS[body["id"]] == body

def test_create_tag_route_non_string_name_returns_422(client):
    response = client.post("/api/tags", json={"name": 123})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid name: must be a string"}

def test_create_tag_route_empty_name_returns_422(client):
    response = client.post("/api/tags", json={"name": "   "})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid name: cannot be empty"}

def test_create_tag_route_duplicate_name_returns_422(client):
    client.post("/api/tags", json={"name": "work"})
    response = client.post("/api/tags", json={"name": "Work"})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid name: already exists"}
