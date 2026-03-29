"""
Test file for TopBass new features iteration 10:
1. Location-based services / geolocation (nearby district search)
2. CSV import for bulk handyman onboarding
3. Analytics dashboard for admin
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://topbass-staging.preview.emergentagent.com')

# Admin credentials
ADMIN_EMAIL = "admin@bassbass.lk"
ADMIN_PASSWORD = "admin123"

class TestNearbyDistricts:
    """Test nearby districts endpoints for location-based services"""
    
    def test_nearby_districts_colombo(self):
        """GET /api/districts/nearby - Returns nearby districts with distances"""
        response = requests.get(f"{BASE_URL}/api/districts/nearby?district=Colombo&radius=80")
        assert response.status_code == 200
        
        data = response.json()
        assert "district" in data
        assert data["district"] == "Colombo"
        assert "radius_km" in data
        assert data["radius_km"] == 80
        assert "nearby" in data
        assert isinstance(data["nearby"], list)
        
        # Colombo should be in its own nearby list with distance 0
        colombo_entry = next((d for d in data["nearby"] if d["district"] == "Colombo"), None)
        assert colombo_entry is not None
        assert colombo_entry["distance_km"] == 0.0
        
        # Gampaha should be nearby (about 24km)
        gampaha_entry = next((d for d in data["nearby"] if d["district"] == "Gampaha"), None)
        assert gampaha_entry is not None
        assert gampaha_entry["distance_km"] < 30  # Should be around 24km
        
        print(f"✓ Nearby districts from Colombo: {len(data['nearby'])} districts found")
    
    def test_nearby_districts_kandy(self):
        """GET /api/districts/nearby - Kandy should have different nearby districts"""
        response = requests.get(f"{BASE_URL}/api/districts/nearby?district=Kandy&radius=100")
        assert response.status_code == 200
        
        data = response.json()
        assert data["district"] == "Kandy"
        assert len(data["nearby"]) > 0
        
        # Matale should be near Kandy
        matale_entry = next((d for d in data["nearby"] if d["district"] == "Matale"), None)
        assert matale_entry is not None
        print(f"✓ Nearby districts from Kandy: {len(data['nearby'])} districts found")
    
    def test_nearby_districts_invalid(self):
        """GET /api/districts/nearby - Invalid district returns empty nearby"""
        response = requests.get(f"{BASE_URL}/api/districts/nearby?district=InvalidDistrict&radius=80")
        assert response.status_code == 200
        
        data = response.json()
        assert data["nearby"] == []
        print("✓ Invalid district returns empty nearby list")


class TestNearbyHandymen:
    """Test nearby handymen endpoint for location-based services"""
    
    def test_nearby_handymen_colombo(self):
        """GET /api/handymen/nearby - Returns handymen sorted by proximity"""
        response = requests.get(f"{BASE_URL}/api/handymen/nearby?district=Colombo")
        assert response.status_code == 200
        
        data = response.json()
        assert "handymen" in data
        assert "total" in data
        assert "from_district" in data
        assert data["from_district"] == "Colombo"
        
        # If there are handymen, check distance_km field
        if len(data["handymen"]) > 0:
            for h in data["handymen"]:
                assert "distance_km" in h
                assert h["distance_km"] >= 0
        
        print(f"✓ Nearby handymen from Colombo: {data['total']} found")
    
    def test_nearby_handymen_with_service_filter(self):
        """GET /api/handymen/nearby - Filter by service"""
        response = requests.get(f"{BASE_URL}/api/handymen/nearby?district=Colombo&service=plumber")
        assert response.status_code == 200
        
        data = response.json()
        # All returned handymen should have plumber in services
        for h in data["handymen"]:
            assert "plumber" in h.get("services", [])
        
        print(f"✓ Nearby plumbers from Colombo: {data['total']} found")
    
    def test_nearby_handymen_sorted_by_distance(self):
        """GET /api/handymen/nearby - Handymen should be sorted by distance"""
        response = requests.get(f"{BASE_URL}/api/handymen/nearby?district=Colombo&limit=20")
        assert response.status_code == 200
        
        data = response.json()
        distances = [h["distance_km"] for h in data["handymen"]]
        
        # Check that distances are in non-decreasing order (sorted)
        for i in range(len(distances) - 1):
            assert distances[i] <= distances[i + 1], "Handymen should be sorted by distance"
        
        print(f"✓ Handymen are sorted by distance")
    
    def test_nearby_handymen_with_radius(self):
        """GET /api/handymen/nearby - Custom radius parameter"""
        response = requests.get(f"{BASE_URL}/api/handymen/nearby?district=Colombo&radius=50")
        assert response.status_code == 200
        
        data = response.json()
        # All handymen should be within 50km radius
        for h in data["handymen"]:
            assert h["distance_km"] <= 50, f"Handyman should be within 50km radius, got {h['distance_km']}km"
        
        print(f"✓ All handymen within 50km radius")


class TestAdminCSVImport:
    """Test CSV import functionality for bulk handyman onboarding"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_csv_template_download(self, admin_token):
        """GET /api/admin/csv-template - Download CSV template"""
        response = requests.get(f"{BASE_URL}/api/admin/csv-template")
        assert response.status_code == 200
        
        content = response.text
        # Check template has expected columns
        assert "full_name" in content
        assert "email" in content
        assert "phone" in content
        assert "password" in content
        assert "district" in content
        assert "services" in content
        assert "description" in content
        assert "experience_years" in content
        
        # Check example row exists
        assert "kamal@example.com" in content.lower() or "Kamal" in content
        
        print("✓ CSV template has all required columns")
    
    def test_csv_import_valid(self, admin_token):
        """POST /api/admin/csv-import - Upload valid CSV"""
        import uuid
        unique = uuid.uuid4().hex[:6]
        
        csv_content = f"""full_name,email,phone,password,district,services,description,experience_years
TEST CSV User {unique},test_csv_{unique}@test.com,0771234567,testpass123,Colombo,plumber,Test CSV import,3"""
        
        files = {'file': ('test_import.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(f"{BASE_URL}/api/admin/csv-import", files=files, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert data["results"]["created"] >= 1
        print(f"✓ CSV import successful: {data['results']['created']} created, {data['results']['skipped']} skipped")
    
    def test_csv_import_duplicate_email(self, admin_token):
        """POST /api/admin/csv-import - Duplicate email should be skipped"""
        # Use existing admin email
        csv_content = f"""full_name,email,phone,password,district,services,description,experience_years
Duplicate User,{ADMIN_EMAIL},0771234567,testpass123,Colombo,plumber,Test duplicate,3"""
        
        files = {'file': ('test_dup.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(f"{BASE_URL}/api/admin/csv-import", files=files, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["results"]["skipped"] >= 1
        assert any("Email already exists" in e.get("reason", "") for e in data["results"]["errors"])
        print("✓ Duplicate email correctly skipped")
    
    def test_csv_import_missing_required_fields(self, admin_token):
        """POST /api/admin/csv-import - Missing required fields should be skipped"""
        csv_content = """full_name,email,phone,password,district,services,description,experience_years
,missing_email_row@test.com,0771234567,testpass123,Colombo,plumber,Missing name,3
Test User Without Email,,0771234567,testpass123,Colombo,plumber,Missing email,3"""
        
        files = {'file': ('test_missing.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(f"{BASE_URL}/api/admin/csv-import", files=files, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["results"]["skipped"] >= 2
        print("✓ Missing required fields correctly skipped")
    
    def test_csv_import_non_csv_file(self, admin_token):
        """POST /api/admin/csv-import - Non-CSV file should be rejected"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        files = {'file': ('test.txt', io.BytesIO(b"not a csv"), 'text/plain')}
        
        response = requests.post(f"{BASE_URL}/api/admin/csv-import", files=files, headers=headers)
        assert response.status_code == 400
        assert "CSV" in response.json().get("detail", "")
        print("✓ Non-CSV file correctly rejected")
    
    def test_csv_import_requires_admin(self):
        """POST /api/admin/csv-import - Requires admin authentication"""
        csv_content = """full_name,email,phone,password,district,services,description,experience_years
Test User,test@test.com,0771234567,testpass123,Colombo,plumber,Test,3"""
        
        files = {'file': ('test.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
        
        # Without auth
        response = requests.post(f"{BASE_URL}/api/admin/csv-import", files=files)
        assert response.status_code == 401
        print("✓ CSV import requires authentication")


class TestAdminAnalytics:
    """Test analytics dashboard endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_analytics_endpoint_structure(self, admin_token):
        """GET /api/admin/analytics - Returns expected data structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check all expected keys exist
        expected_keys = [
            "bookings_by_status",
            "bookings_daily",
            "top_services",
            "top_handymen",
            "user_growth",
            "bookings_by_district",
            "revenue_summary",
            "totals"
        ]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"
        
        print("✓ Analytics endpoint returns all expected keys")
    
    def test_analytics_bookings_by_status(self, admin_token):
        """GET /api/admin/analytics - bookings_by_status structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        data = response.json()
        
        # bookings_by_status should be a dict with status names as keys
        assert isinstance(data["bookings_by_status"], dict)
        
        # Values should be integers
        for status, count in data["bookings_by_status"].items():
            assert isinstance(count, int)
            assert count >= 0
        
        print(f"✓ Bookings by status: {data['bookings_by_status']}")
    
    def test_analytics_bookings_daily(self, admin_token):
        """GET /api/admin/analytics - bookings_daily structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        data = response.json()
        
        assert isinstance(data["bookings_daily"], list)
        
        # Each entry should have date, count, revenue
        for entry in data["bookings_daily"]:
            assert "date" in entry
            assert "count" in entry
            assert "revenue" in entry
            assert isinstance(entry["count"], int)
        
        print(f"✓ Bookings daily: {len(data['bookings_daily'])} days of data")
    
    def test_analytics_top_services(self, admin_token):
        """GET /api/admin/analytics - top_services structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        data = response.json()
        
        assert isinstance(data["top_services"], list)
        
        # Each entry should have service_id and bookings
        for entry in data["top_services"]:
            assert "service_id" in entry
            assert "bookings" in entry
        
        print(f"✓ Top services: {data['top_services']}")
    
    def test_analytics_top_handymen(self, admin_token):
        """GET /api/admin/analytics - top_handymen structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        data = response.json()
        
        assert isinstance(data["top_handymen"], list)
        
        # Each entry should have expected fields
        for entry in data["top_handymen"]:
            assert "full_name" in entry
            assert "user_id" in entry
        
        print(f"✓ Top handymen: {len(data['top_handymen'])} entries")
    
    def test_analytics_user_growth(self, admin_token):
        """GET /api/admin/analytics - user_growth structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        data = response.json()
        
        assert isinstance(data["user_growth"], list)
        
        # Each entry should have date and role counts
        for entry in data["user_growth"]:
            assert "date" in entry
            # Should have customer, handyman, shop keys
            assert "customer" in entry or "handyman" in entry or "shop" in entry
        
        print(f"✓ User growth: {len(data['user_growth'])} days of data")
    
    def test_analytics_bookings_by_district(self, admin_token):
        """GET /api/admin/analytics - bookings_by_district structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        data = response.json()
        
        assert isinstance(data["bookings_by_district"], list)
        
        for entry in data["bookings_by_district"]:
            assert "district" in entry
            assert "count" in entry
        
        print(f"✓ Bookings by district: {data['bookings_by_district']}")
    
    def test_analytics_revenue_summary(self, admin_token):
        """GET /api/admin/analytics - revenue_summary structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        data = response.json()
        
        revenue = data["revenue_summary"]
        assert "total_revenue" in revenue
        assert "total_platform_fee" in revenue
        assert "total_transactions" in revenue
        
        print(f"✓ Revenue summary: {revenue}")
    
    def test_analytics_totals(self, admin_token):
        """GET /api/admin/analytics - totals structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        data = response.json()
        
        totals = data["totals"]
        assert "users" in totals
        assert "handymen" in totals
        assert "bookings" in totals
        assert "reviews" in totals
        
        assert totals["users"] >= 0
        assert totals["handymen"] >= 0
        assert totals["bookings"] >= 0
        assert totals["reviews"] >= 0
        
        print(f"✓ Totals: {totals}")
    
    def test_analytics_requires_admin(self):
        """GET /api/admin/analytics - Requires admin authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        assert response.status_code == 401
        print("✓ Analytics requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
