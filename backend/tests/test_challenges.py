"""
Test suite for Daily/Weekly Challenges feature
Tests: /api/challenges, /api/challenges/{id}/start, /api/challenges/{id}/complete-task, /api/challenges/{id}/complete
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_TEACHER_EMAIL = "testteacher123@test.com"
TEST_TEACHER_PASSWORD = "test1234"


class TestChallengesAPI:
    """Test Daily/Weekly Challenges API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/login", json={
            "email": TEST_TEACHER_EMAIL,
            "password": TEST_TEACHER_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_get_challenges_returns_daily_and_weekly(self):
        """Test GET /api/challenges returns both daily and weekly challenges"""
        response = self.session.get(f"{BASE_URL}/api/challenges")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify structure
        assert "daily" in data, "Response should contain 'daily' challenge"
        assert "weekly" in data, "Response should contain 'weekly' challenge"
        
        # Verify daily challenge structure
        daily = data["daily"]
        assert "id" in daily, "Daily challenge should have 'id'"
        assert "title" in daily, "Daily challenge should have 'title'"
        assert "description" in daily, "Daily challenge should have 'description'"
        assert "tasks" in daily, "Daily challenge should have 'tasks'"
        assert "points_reward" in daily, "Daily challenge should have 'points_reward'"
        assert "xp_reward" in daily, "Daily challenge should have 'xp_reward'"
        assert "challenge_type" in daily, "Daily challenge should have 'challenge_type'"
        assert daily["challenge_type"] == "daily", "Daily challenge type should be 'daily'"
        
        # Verify weekly challenge structure
        weekly = data["weekly"]
        assert "id" in weekly, "Weekly challenge should have 'id'"
        assert "title" in weekly, "Weekly challenge should have 'title'"
        assert "description" in weekly, "Weekly challenge should have 'description'"
        assert "tasks" in weekly, "Weekly challenge should have 'tasks'"
        assert "points_reward" in weekly, "Weekly challenge should have 'points_reward'"
        assert "xp_reward" in weekly, "Weekly challenge should have 'xp_reward'"
        assert "challenge_type" in weekly, "Weekly challenge should have 'challenge_type'"
        assert weekly["challenge_type"] == "weekly", "Weekly challenge type should be 'weekly'"
        
        print(f"✅ Daily challenge: {daily['title']} - {daily['points_reward']} points, {daily['xp_reward']} XP")
        print(f"✅ Weekly challenge: {weekly['title']} - {weekly['points_reward']} points, {weekly['xp_reward']} XP")
    
    def test_daily_challenge_has_tasks(self):
        """Test daily challenge contains tasks list"""
        response = self.session.get(f"{BASE_URL}/api/challenges")
        
        assert response.status_code == 200
        
        daily = response.json()["daily"]
        tasks = daily["tasks"]
        
        assert isinstance(tasks, list), "Tasks should be a list"
        assert len(tasks) > 0, "Daily challenge should have at least one task"
        
        # Verify task structure
        for task in tasks:
            assert "id" in task, "Task should have 'id'"
            assert "title" in task, "Task should have 'title'"
        
        print(f"✅ Daily challenge has {len(tasks)} tasks")
    
    def test_weekly_challenge_has_tasks(self):
        """Test weekly challenge contains tasks list"""
        response = self.session.get(f"{BASE_URL}/api/challenges")
        
        assert response.status_code == 200
        
        weekly = response.json()["weekly"]
        tasks = weekly["tasks"]
        
        assert isinstance(tasks, list), "Tasks should be a list"
        assert len(tasks) > 0, "Weekly challenge should have at least one task"
        
        # Verify task structure
        for task in tasks:
            assert "id" in task, "Task should have 'id'"
            assert "title" in task, "Task should have 'title'"
        
        print(f"✅ Weekly challenge has {len(tasks)} tasks")
    
    def test_challenges_have_time_remaining(self):
        """Test challenges include time_remaining field"""
        response = self.session.get(f"{BASE_URL}/api/challenges")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Check daily time remaining
        assert "time_remaining" in data["daily"], "Daily challenge should have time_remaining"
        daily_time = data["daily"]["time_remaining"]
        assert "hours" in daily_time or "formatted" in daily_time, "time_remaining should have hours or formatted"
        
        # Check weekly time remaining
        assert "time_remaining" in data["weekly"], "Weekly challenge should have time_remaining"
        weekly_time = data["weekly"]["time_remaining"]
        assert "hours" in weekly_time or "formatted" in weekly_time, "time_remaining should have hours or formatted"
        
        print(f"✅ Daily time remaining: {daily_time.get('formatted', 'N/A')}")
        print(f"✅ Weekly time remaining: {weekly_time.get('formatted', 'N/A')}")
    
    def test_challenges_have_status(self):
        """Test challenges include status field"""
        response = self.session.get(f"{BASE_URL}/api/challenges")
        
        assert response.status_code == 200
        
        data = response.json()
        
        assert "status" in data["daily"], "Daily challenge should have status"
        assert "status" in data["weekly"], "Weekly challenge should have status"
        
        # Status should be one of: active, upcoming, expired
        valid_statuses = ["active", "upcoming", "expired"]
        assert data["daily"]["status"] in valid_statuses, f"Invalid daily status: {data['daily']['status']}"
        assert data["weekly"]["status"] in valid_statuses, f"Invalid weekly status: {data['weekly']['status']}"
        
        print(f"✅ Daily status: {data['daily']['status']}")
        print(f"✅ Weekly status: {data['weekly']['status']}")
    
    def test_challenges_require_authentication(self):
        """Test /api/challenges requires authentication"""
        # Create new session without auth
        no_auth_session = requests.Session()
        response = no_auth_session.get(f"{BASE_URL}/api/challenges")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✅ Challenges endpoint requires authentication")
    
    def test_start_challenge_endpoint(self):
        """Test POST /api/challenges/{id}/start endpoint"""
        # First get a challenge ID
        challenges_response = self.session.get(f"{BASE_URL}/api/challenges")
        assert challenges_response.status_code == 200
        
        daily_id = challenges_response.json()["daily"]["id"]
        
        # Try to start the challenge
        response = self.session.post(f"{BASE_URL}/api/challenges/{daily_id}/start")
        
        # Should return 200 (started or already started)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "message" in data, "Response should have message"
        print(f"✅ Start challenge response: {data['message']}")
    
    def test_complete_task_requires_task_id(self):
        """Test POST /api/challenges/{id}/complete-task requires task_id"""
        # First get a challenge ID
        challenges_response = self.session.get(f"{BASE_URL}/api/challenges")
        assert challenges_response.status_code == 200
        
        daily_id = challenges_response.json()["daily"]["id"]
        
        # Try to complete task without task_id
        response = self.session.post(
            f"{BASE_URL}/api/challenges/{daily_id}/complete-task",
            json={}
        )
        
        # Should return 400 (bad request)
        assert response.status_code == 400, f"Expected 400 without task_id, got {response.status_code}"
        print("✅ Complete task endpoint validates task_id")


class TestPayPalCurrencyConversion:
    """Test PayPal currency conversion display"""
    
    def test_paypal_pricing_returns_usd(self):
        """Test /api/paypal/pricing returns USD prices"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/paypal/pricing")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        assert "currency" in data, "Response should have currency"
        assert data["currency"] == "USD", "Currency should be USD"
        assert "prices" in data, "Response should have prices"
        
        prices = data["prices"]
        
        # Verify price structure: prices[subscription_type][age_group]
        for sub_type in ["monthly", "quarterly"]:
            assert sub_type in prices, f"Prices should include {sub_type} subscription type"
            sub_prices = prices[sub_type]
            
            for age_group in ["5-8", "9-12", "13-16"]:
                assert age_group in sub_prices, f"{sub_type} should have {age_group} age group"
                price = sub_prices[age_group]
                
                # Verify prices are in expected USD range
                if sub_type == "monthly":
                    assert 10 <= price <= 30, f"Monthly price ${price} for {age_group} should be in reasonable USD range"
                else:
                    assert 30 <= price <= 80, f"Quarterly price ${price} for {age_group} should be in reasonable USD range"
        
        print(f"✅ PayPal pricing returns USD prices for all age groups")
        print(f"   Monthly: 5-8=${prices['monthly']['5-8']}, 9-12=${prices['monthly']['9-12']}, 13-16=${prices['monthly']['13-16']}")
        print(f"   Quarterly: 5-8=${prices['quarterly']['5-8']}, 9-12=${prices['quarterly']['9-12']}, 13-16=${prices['quarterly']['13-16']}")


class TestLandingPage:
    """Test landing page features"""
    
    def test_api_root_accessible(self):
        """Test API root endpoint is accessible"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✅ API root endpoint accessible")
    
    def test_subscription_plans_accessible(self):
        """Test subscription plans endpoint is accessible"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/subscription/plans")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        print("✅ Subscription plans endpoint accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
