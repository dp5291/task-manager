import copy

import pytest
from app import app
from services.users import USERS, get_notification_pref, list_users, set_notification_pref
from utils.errors import NotFoundError, ValidationError


@pytest.fixture(autouse=True)
def restore_users():
    snapshot = copy.deepcopy(USERS)
    yield
    USERS.clear()
    USERS.update(snapshot)


@pytest.fixture
def client():
    return app.test_client()


# Service tests

def test_seed_users_default_to_none():
    assert all(user["notification_pref"] == "none" for user in list_users())
    assert get_notification_pref(1) == "none"
    assert get_notification_pref(2) == "none"

@pytest.mark.parametrize("pref", ["email", "sms", "none"])
def test_set_notification_pref_accepts_valid_values(pref):
    result = set_notification_pref(1, pref)
    assert result["notification_pref"] == pref
    assert get_notification_pref(1) == pref

def test_set_notification_pref_invalid_value_raises_validation_error():
    with pytest.raises(ValidationError):
        set_notification_pref(1, "pigeon")
    assert get_notification_pref(1) == "none"

def test_set_notification_pref_unknown_user_raises_not_found():
    with pytest.raises(NotFoundError):
        set_notification_pref(999, "email")


# Route tests

def test_list_users_route_includes_notification_pref(client):
    response = client.get("/api/users")
    assert response.status_code == 200
    users = response.get_json()
    assert users
    assert all("notification_pref" in user for user in users)

def test_get_user_route_includes_notification_pref(client):
    response = client.get("/api/users/1")
    assert response.status_code == 200
    assert response.get_json()["notification_pref"] == "none"

def test_get_notification_pref_route_returns_pref(client):
    response = client.get("/api/users/1/notifications")
    assert response.status_code == 200
    assert response.get_json() == {"user_id": 1, "notification_pref": "none"}

def test_patch_notification_pref_route_valid_returns_200(client):
    response = client.patch("/api/users/1/notifications", json={"notification_pref": "email"})
    assert response.status_code == 200
    assert response.get_json()["notification_pref"] == "email"
    assert client.get("/api/users/1/notifications").get_json()["notification_pref"] == "email"

def test_patch_notification_pref_route_invalid_returns_422(client):
    response = client.patch("/api/users/1/notifications", json={"notification_pref": "pigeon"})
    assert response.status_code == 422
    assert "error" in response.get_json()

def test_get_notification_pref_route_unknown_user_returns_404(client):
    response = client.get("/api/users/999/notifications")
    assert response.status_code == 404
    assert "error" in response.get_json()

def test_patch_notification_pref_route_unknown_user_returns_404(client):
    response = client.patch("/api/users/999/notifications", json={"notification_pref": "email"})
    assert response.status_code == 404
    assert "error" in response.get_json()

def test_get_user_route_unknown_user_returns_404(client):
    response = client.get("/api/users/999")
    assert response.status_code == 404
