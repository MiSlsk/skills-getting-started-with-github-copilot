from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def api_client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))

    with TestClient(app_module.app) as client:
        yield client


def test_root_redirects_to_frontend(api_client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = api_client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(api_client):
    # Arrange
    activity_name = "Art Club"

    # Act
    response = api_client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[activity_name]["participants"] == []


def test_signup_adds_participant_to_activity(api_client):
    # Arrange
    activity_path = "/activities/Art%20Club/signup"
    email = "student@example.com"

    # Act
    response = api_client.post(activity_path, params={"email": email})
    activities_response = api_client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Art Club"}
    assert email in activities_response.json()["Art Club"]["participants"]


def test_signup_rejects_unknown_activity(api_client):
    # Arrange
    activity_path = "/activities/Unknown%20Activity/signup"
    email = "student@example.com"

    # Act
    response = api_client.post(activity_path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(api_client):
    # Arrange
    activity_path = "/activities/Chess%20Club/signup"
    email = "michael@mergington.edu"

    # Act
    response = api_client.post(activity_path, params={"email": email})
    activities_response = api_client.get("/activities")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities_response.json()["Chess Club"]["participants"].count(email) == 1


def test_delete_removes_participant_from_activity(api_client):
    # Arrange
    activity_path = "/activities/Chess%20Club/signup"
    email = "michael@mergington.edu"

    # Act
    response = api_client.delete(activity_path, params={"email": email})
    activities_response = api_client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    assert email not in activities_response.json()["Chess Club"]["participants"]


def test_delete_rejects_unknown_activity(api_client):
    # Arrange
    activity_path = "/activities/Unknown%20Activity/signup"
    email = "student@example.com"

    # Act
    response = api_client.delete(activity_path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_delete_rejects_unregistered_participant(api_client):
    # Arrange
    activity_path = "/activities/Art%20Club/signup"
    email = "student@example.com"

    # Act
    response = api_client.delete(activity_path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_removed_participant_can_sign_up_again(api_client):
    # Arrange
    activity_path = "/activities/Chess%20Club/signup"
    email = "michael@mergington.edu"

    # Act
    delete_response = api_client.delete(activity_path, params={"email": email})
    signup_response = api_client.post(activity_path, params={"email": email})
    activities_response = api_client.get("/activities")

    # Assert
    assert delete_response.status_code == 200
    assert signup_response.status_code == 200
    assert activities_response.json()["Chess Club"]["participants"].count(email) == 1