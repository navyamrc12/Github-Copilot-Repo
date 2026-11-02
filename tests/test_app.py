from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities_response = response.json()
    assert "Chess Club" in activities_response
    assert set(activities_response["Chess Club"]) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }


def test_signup_adds_participant(client):
    activity_name = "Chess Club"
    email = "new-student@mergington.edu"

    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    updated_activities = client.get("/activities").json()
    assert email in updated_activities[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    updated_activities = client.get("/activities").json()
    assert email not in updated_activities[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_unregistered_participant(client):
    response = client.delete(
        "/activities/Chess%20Club/participants",
        params={"email": "not-signed-up@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_root_redirects_to_activity_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"