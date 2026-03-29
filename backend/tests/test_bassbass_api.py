"""
Niyama Bassa (BassBass) Handyman Marketplace API Tests
Tests for: Auth, Services, Handyman Profiles, Bookings, Reviews, Admin
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data
TEST_CUSTOMER_EMAIL = f"test_customer_{uuid.uuid4().hex[:8]}@test.lk"
TEST_HANDYMAN_EMAIL = f"test_handyman_{uuid.uuid4().hex[:8]}@test.lk"
TEST_PASSWORD = "testpass123"
ADMIN_EMAIL = "admin@bassbass.lk"
ADMIN_PASSWORD = "admin123"


class TestAPIHealth:
    """API Health and Root Endpoint Tests"""
    
    def test_api_root(self):
        """Test API root endpoint returns expected response"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Niyama Bassa API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"
        print(f"API Health: {data['name']} v{data['version']} - {data['status']}")


class TestServicesEndpoint:
    """Test /api/services - Service Categories and Districts"""
    
    def test_get_services(self):
        """Test GET /api/services returns 19 services and 25 districts"""
        response = requests.get(f"{BASE_URL}/api/services")
        assert response.status_code == 200
        data = response.json()
        
        # Validate services
        assert "services" in data
        assert len(data["services"]) == 19, f"Expected 19 services, got {len(data['services'])}"
        
        # Validate districts
        assert "districts" in data
        assert len(data["districts"]) == 25, f"Expected 25 districts, got {len(data['districts'])}"
        
        # Check service structure
        service = data["services"][0]
        assert "id" in service
        assert "name_en" in service
        assert "name_si" in service
        assert "name_ta" in service
        assert "icon" in service
        
        print(f"Services: {len(data['services'])} categories, Districts: {len(data['districts'])}")


class TestUserRegistration:
    """Test user registration for different roles"""
    
    def test_register_customer(self):
        """Test POST /api/auth/register for customer role"""
        payload = {
            "email": TEST_CUSTOMER_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Test Customer",
            "phone": "0771234567",
            "role": "customer",
            "district": "Colombo"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_CUSTOMER_EMAIL
        assert data["user"]["role"] == "customer"
        assert data["user"]["is_approved"] == True  # Customers auto-approved
        print(f"Customer registered: {data['user']['email']}")
        return data["access_token"]
    
    def test_register_handyman(self):
        """Test POST /api/auth/register for handyman role"""
        payload = {
            "email": TEST_HANDYMAN_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Test Handyman",
            "phone": "0779876543",
            "role": "handyman",
            "district": "Gampaha"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["user"]["role"] == "handyman"
        assert data["user"]["is_approved"] == False  # Handymen need approval
        assert "Awaiting admin approval" in data["message"]
        print(f"Handyman registered: {data['user']['email']} (pending approval)")
        return data["access_token"]
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails"""
        payload = {
            "email": ADMIN_EMAIL,  # Already exists
            "password": TEST_PASSWORD,
            "full_name": "Duplicate User",
            "phone": "0771111111",
            "role": "customer",
            "district": "Colombo"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()


class TestUserLogin:
    """Test user login with valid/invalid credentials"""
    
    def test_admin_login(self):
        """Test admin login with admin@bassbass.lk / admin123"""
        payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"Admin login successful: {data['user']['full_name']}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        payload = {"email": "wrong@email.com", "password": "wrongpassword"}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_wrong_password(self):
        """Test login with wrong password returns 401"""
        payload = {"email": ADMIN_EMAIL, "password": "wrongpassword"}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 401


class TestAuthMe:
    """Test /api/auth/me endpoint"""
    
    def test_get_me_authenticated(self):
        """Test GET /api/auth/me with valid token"""
        # First login
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        token = login_res.json()["access_token"]
        
        # Get me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == ADMIN_EMAIL
    
    def test_get_me_unauthenticated(self):
        """Test GET /api/auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


class TestHandymenList:
    """Test /api/handymen listing endpoint"""
    
    def test_list_handymen(self):
        """Test GET /api/handymen returns paginated list"""
        response = requests.get(f"{BASE_URL}/api/handymen")
        assert response.status_code == 200
        data = response.json()
        
        assert "handymen" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        print(f"Handymen list: {data['total']} total, page {data['page']}/{data['pages']}")
    
    def test_list_handymen_filter_service(self):
        """Test GET /api/handymen with service filter"""
        response = requests.get(f"{BASE_URL}/api/handymen?service=plumber")
        assert response.status_code == 200
        data = response.json()
        assert "handymen" in data
    
    def test_list_handymen_filter_district(self):
        """Test GET /api/handymen with district filter"""
        response = requests.get(f"{BASE_URL}/api/handymen?district=Colombo")
        assert response.status_code == 200
        data = response.json()
        assert "handymen" in data


class TestHandymanProfile:
    """Test handyman profile creation and retrieval"""
    
    @pytest.fixture
    def handyman_token(self):
        """Create a new handyman and return token"""
        email = f"test_hm_{uuid.uuid4().hex[:8]}@test.lk"
        reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": TEST_PASSWORD,
            "full_name": "Profile Test Handyman",
            "phone": "0771112222",
            "role": "handyman",
            "district": "Kandy"
        })
        return reg_res.json()["access_token"]
    
    def test_create_profile(self, handyman_token):
        """Test POST /api/handyman/profile to create profile"""
        payload = {
            "services": ["plumber", "electrician"],
            "description": "Experienced plumber and electrician",
            "experience_years": 5,
            "districts_served": ["Kandy", "Matale"],
            "hourly_rate": 1500,
            "phone": "0771112222",
            "whatsapp": "+94771112222"
        }
        response = requests.post(f"{BASE_URL}/api/handyman/profile", json=payload, headers={
            "Authorization": f"Bearer {handyman_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Profile saved"
        assert data["profile"]["services"] == ["plumber", "electrician"]
        assert data["profile"]["experience_years"] == 5
        print(f"Profile created: {data['profile']['services']}")
    
    def test_get_my_profile(self, handyman_token):
        """Test GET /api/handyman/my-profile"""
        response = requests.get(f"{BASE_URL}/api/handyman/my-profile", headers={
            "Authorization": f"Bearer {handyman_token}"
        })
        assert response.status_code == 200


class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return login_res.json()["access_token"]
    
    @pytest.fixture
    def customer_token(self):
        """Get customer token for unauthorized tests"""
        email = f"test_cust_{uuid.uuid4().hex[:8]}@test.lk"
        reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": TEST_PASSWORD,
            "full_name": "Test Customer",
            "phone": "0773334444",
            "role": "customer",
            "district": "Colombo"
        })
        return reg_res.json()["access_token"]
    
    def test_admin_statistics(self, admin_token):
        """Test GET /api/admin/statistics returns all stats"""
        response = requests.get(f"{BASE_URL}/api/admin/statistics", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        expected_fields = [
            "total_customers", "total_handymen", "approved_handymen",
            "pending_approvals", "total_bookings", "active_bookings",
            "completed_bookings", "total_reviews"
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"Admin stats: Customers={data['total_customers']}, Handymen={data['total_handymen']}, Pending={data['pending_approvals']}")
    
    def test_admin_pending_approvals(self, admin_token):
        """Test GET /api/admin/pending-approvals"""
        response = requests.get(f"{BASE_URL}/api/admin/pending-approvals", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        print(f"Pending approvals: {len(data['pending'])}")
    
    def test_admin_users_list(self, admin_token):
        """Test GET /api/admin/users"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        print(f"Total users: {len(data['users'])}")
    
    def test_admin_users_filter_role(self, admin_token):
        """Test GET /api/admin/users with role filter"""
        response = requests.get(f"{BASE_URL}/api/admin/users?role=customer", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        for user in data["users"]:
            assert user["role"] == "customer"
    
    def test_admin_statistics_unauthorized(self, customer_token):
        """Test admin endpoint returns 403 for non-admin"""
        response = requests.get(f"{BASE_URL}/api/admin/statistics", headers={
            "Authorization": f"Bearer {customer_token}"
        })
        assert response.status_code == 403


class TestApprovalFlow:
    """Test admin approve/reject handyman flow"""
    
    def test_approve_handyman_flow(self):
        """Test full approve flow: register handyman -> admin approves -> verify"""
        # 1. Register new handyman
        email = f"approve_test_{uuid.uuid4().hex[:8]}@test.lk"
        reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": TEST_PASSWORD,
            "full_name": "Approval Test",
            "phone": "0775556666",
            "role": "handyman",
            "district": "Galle"
        })
        assert reg_res.status_code == 200
        user_id = reg_res.json()["user"]["id"]
        
        # 2. Login as admin
        admin_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        admin_token = admin_res.json()["access_token"]
        
        # 3. Approve the user
        approve_res = requests.put(f"{BASE_URL}/api/admin/approve/{user_id}", json={}, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert approve_res.status_code == 200
        assert "approved" in approve_res.json()["message"].lower()
        print(f"Handyman {email} approved successfully")


class TestBookingFlow:
    """Test booking creation and status management"""
    
    def test_booking_requires_auth(self):
        """Test booking creation requires authentication"""
        payload = {
            "handyman_id": "fake-id",
            "service_id": "plumber",
            "description": "Test booking"
        }
        response = requests.post(f"{BASE_URL}/api/bookings/create", json=payload)
        assert response.status_code == 401
    
    def test_my_bookings_requires_auth(self):
        """Test GET /api/bookings/my requires authentication"""
        response = requests.get(f"{BASE_URL}/api/bookings/my")
        assert response.status_code == 401


class TestReviewEndpoint:
    """Test review creation endpoint"""
    
    def test_review_requires_auth(self):
        """Test review creation requires authentication"""
        payload = {"rating": 5, "comment": "Great service"}
        response = requests.post(f"{BASE_URL}/api/reviews/fake-id", json=payload)
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
