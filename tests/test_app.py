"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities(monkeypatch):
    """Reset activities to a known state before each test"""
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Full Activity": {
            "description": "An activity at max capacity",
            "schedule": "Saturdays, 10:00 AM - 12:00 PM",
            "max_participants": 2,
            "participants": ["participant1@mergington.edu", "participant2@mergington.edu"]
        }
    }
    
    # Clear the existing activities and update with test data
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Test cases for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Full Activity" in data
    
    def test_get_activities_returns_correct_structure(self, client, reset_activities):
        """Test that activities have correct structure with all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        
        assert isinstance(chess_club["participants"], list)
        assert chess_club["max_participants"] == 12
    
    def test_get_activities_shows_current_participants(self, client, reset_activities):
        """Test that activities show current participants"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    """Test cases for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, client, reset_activities):
        """Test successful signup for a new participant"""
        response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        assert "newstudent@mergington.edu" in activities["Programming Class"]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client, reset_activities):
        """Test that signing up the same participant twice fails"""
        # First signup succeeds
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Second signup for same participant fails
        response2 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        assert response2.status_code == 400
        assert "Already signed up" in response2.json()["detail"]
    
    def test_signup_to_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signup to a non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_to_full_activity_fails(self, client, reset_activities):
        """Test that signup to a full activity fails"""
        response = client.post(
            "/activities/Full%20Activity/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]
    
    def test_signup_updates_participant_count(self, client, reset_activities):
        """Test that participant count is updated after signup"""
        # Get initial state
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Gym Class"]["participants"])
        
        # Signup a new participant
        client.post(
            "/activities/Gym%20Class/signup",
            params={"email": "newcomer@mergington.edu"}
        )
        
        # Verify count increased
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()["Gym Class"]["participants"])
        
        assert updated_count == initial_count + 1
    
    def test_signup_with_special_characters_in_email(self, client, reset_activities):
        """Test signup with email containing special characters (URL encoded)"""
        email = "student+test@mergington.edu"
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert email in activities["Chess Club"]["participants"]


class TestUnregisterEndpoint:
    """Test cases for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test successful unregister of an existing participant"""
        # Verify participant exists
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        
        # Unregister
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify participant was removed
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client, reset_activities):
        """Test that unregistering a non-existent participant fails"""
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "nonexistent@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_from_nonexistent_activity_fails(self, client, reset_activities):
        """Test that unregistering from a non-existent activity fails"""
        response = client.post(
            "/activities/Fake%20Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_updates_participant_count(self, client, reset_activities):
        """Test that participant count is updated after unregister"""
        # Get initial state
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        
        # Unregister a participant
        client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        # Verify count decreased
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()["Chess Club"]["participants"])
        
        assert updated_count == initial_count - 1
    
    def test_signup_then_unregister_frees_spot(self, client, reset_activities):
        """Test that unregistering frees up a spot in a full activity"""
        # Activity is at max capacity (2/2)
        assert len(activities["Full Activity"]["participants"]) == 2
        
        # Try to signup (should fail - activity full)
        response1 = client.post(
            "/activities/Full%20Activity/signup",
            params={"email": "waitlist@mergington.edu"}
        )
        assert response1.status_code == 400
        
        # Unregister someone
        client.post(
            "/activities/Full%20Activity/unregister",
            params={"email": "participant1@mergington.edu"}
        )
        
        # Now signup should succeed
        response2 = client.post(
            "/activities/Full%20Activity/signup",
            params={"email": "waitlist@mergington.edu"}
        )
        assert response2.status_code == 200
        assert "waitlist@mergington.edu" in activities["Full Activity"]["participants"]
    
    def test_double_unregister_fails(self, client, reset_activities):
        """Test that unregistering the same participant twice fails"""
        # First unregister succeeds
        response1 = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Second unregister of same participant fails
        response2 = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response2.status_code == 400
        assert "not registered" in response2.json()["detail"]


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_and_see_in_activities(self, client, reset_activities):
        """Test that a new signup appears in the activities list"""
        new_email = "integration@mergington.edu"
        
        # Signup
        signup_response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": new_email}
        )
        assert signup_response.status_code == 200
        
        # Verify in activities list
        activities_response = client.get("/activities")
        programming_participants = activities_response.json()["Programming Class"]["participants"]
        assert new_email in programming_participants
    
    def test_unregister_and_not_in_activities(self, client, reset_activities):
        """Test that an unregistered participant no longer appears in activities"""
        email_to_remove = "daniel@mergington.edu"
        
        # Verify initially present
        initial = client.get("/activities")
        assert email_to_remove in initial.json()["Chess Club"]["participants"]
        
        # Unregister
        unregister_response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": email_to_remove}
        )
        assert unregister_response.status_code == 200
        
        # Verify no longer in activities list
        final = client.get("/activities")
        assert email_to_remove not in final.json()["Chess Club"]["participants"]
    
    def test_multiple_signups_to_different_activities(self, client, reset_activities):
        """Test that a student can signup for multiple different activities"""
        email = "multi@mergington.edu"
        
        # Signup for Chess Club
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Signup for Programming Class
        response2 = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify in both activities
        activities_data = client.get("/activities").json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]
