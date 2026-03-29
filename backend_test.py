#!/usr/bin/env python3
"""
TopBass Backend API Testing
Tests all major API endpoints for the handyman service marketplace
"""

import requests
import sys
import json
from datetime import datetime

class TopBassAPITester:
    def __init__(self, base_url="https://8d82b3ad-8c6e-47c9-b8d3-8ca046aa64f7.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.admin_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)
        if self.token and not headers:
            test_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_services_endpoint(self):
        """Test services and districts endpoint"""
        success, response = self.run_test(
            "Get Services & Districts",
            "GET",
            "services",
            200
        )
        if success:
            services = response.get('services', [])
            districts = response.get('districts', [])
            print(f"   Found {len(services)} services and {len(districts)} districts")
            if len(services) >= 18:  # Should have around 20 services
                print("   ✅ Services count looks good")
            else:
                print(f"   ⚠️  Expected ~20 services, got {len(services)}")
        return success

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@bassbass.lk", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_id = response.get('user', {}).get('id')
            print(f"   ✅ Admin logged in successfully")
            return True
        return False

    def test_customer_register(self):
        """Test customer registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        success, response = self.run_test(
            "Customer Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": f"test_customer_{timestamp}@test.lk",
                "password": "test123",
                "full_name": f"Test Customer {timestamp}",
                "phone": f"077123{timestamp[-4:]}",
                "role": "customer",
                "district": "Colombo"
            }
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user', {}).get('id')
            print(f"   ✅ Customer registered successfully")
            return True
        return False

    def test_handyman_register(self):
        """Test handyman registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        success, response = self.run_test(
            "Handyman Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": f"test_handyman_{timestamp}@test.lk",
                "password": "test123",
                "full_name": f"Test Handyman {timestamp}",
                "phone": f"077456{timestamp[-4:]}",
                "role": "handyman",
                "district": "Gampaha"
            }
        )
        return success

    def test_demo_login(self):
        """Test demo user login"""
        success, response = self.run_test(
            "Demo Customer Login",
            "POST",
            "auth/login",
            200,
            data={"email": "saman@demo.lk", "password": "demo123"}
        )
        return success

    def test_handymen_listing(self):
        """Test handymen listing endpoint"""
        success, response = self.run_test(
            "List Handymen",
            "GET",
            "handymen",
            200
        )
        if success:
            handymen = response.get('handymen', [])
            print(f"   Found {len(handymen)} handymen")
        return success

    def test_top_rated_handymen(self):
        """Test top rated handymen endpoint"""
        success, response = self.run_test(
            "Top Rated Handymen",
            "GET",
            "handymen/top-rated",
            200
        )
        if success:
            handymen = response.get('handymen', [])
            print(f"   Found {len(handymen)} top rated handymen")
        return success

    def test_nearby_handymen(self):
        """Test nearby handymen endpoint"""
        success, response = self.run_test(
            "Nearby Handymen",
            "GET",
            "handymen/nearby?district=Colombo&radius=80&limit=6",
            200
        )
        if success:
            handymen = response.get('handymen', [])
            print(f"   Found {len(handymen)} nearby handymen")
        return success

    def test_search_handymen(self):
        """Test handymen search"""
        success, response = self.run_test(
            "Search Handymen",
            "GET",
            "handymen?q=plumber&district=Colombo",
            200
        )
        if success:
            handymen = response.get('handymen', [])
            print(f"   Found {len(handymen)} handymen matching search")
        return success

    def test_admin_stats(self):
        """Test admin statistics endpoint"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        success, response = self.run_test(
            "Admin Statistics",
            "GET",
            "admin/statistics",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        if success:
            stats = response
            print(f"   Total customers: {stats.get('total_customers', 0)}")
            print(f"   Total handymen: {stats.get('total_handymen', 0)}")
            print(f"   Total bookings: {stats.get('total_bookings', 0)}")
        return success

    def test_seed_demo_data(self):
        """Test seeding demo data"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        success, response = self.run_test(
            "Seed Demo Data",
            "POST",
            "admin/seed-demo",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        if success:
            print(f"   Demo data seeded: {response.get('seeded', False)}")
            print(f"   Handymen created: {response.get('handymen_created', 0)}")
            print(f"   Customers created: {response.get('customers_created', 0)}")
        return success

    def test_auth_me(self):
        """Test current user endpoint"""
        if not self.token:
            print("❌ No user token available")
            return False
            
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        if success:
            user = response.get('user', {})
            print(f"   Current user: {user.get('full_name', 'Unknown')}")
        return success

def main():
    print("🚀 Starting TopBass Backend API Tests")
    print("=" * 50)
    
    tester = TopBassAPITester()
    
    # Test basic endpoints first
    print("\n📋 Testing Basic Endpoints")
    tester.test_services_endpoint()
    
    # Test authentication
    print("\n🔐 Testing Authentication")
    tester.test_admin_login()
    tester.test_customer_register()
    tester.test_handyman_register()
    tester.test_demo_login()
    tester.test_auth_me()
    
    # Test handymen endpoints
    print("\n👷 Testing Handymen Endpoints")
    tester.test_handymen_listing()
    tester.test_top_rated_handymen()
    tester.test_nearby_handymen()
    tester.test_search_handymen()
    
    # Test admin endpoints
    print("\n👑 Testing Admin Endpoints")
    tester.test_seed_demo_data()
    tester.test_admin_stats()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✅ Backend API tests mostly successful!")
        return 0
    else:
        print("❌ Backend API has significant issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())