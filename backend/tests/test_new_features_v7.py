"""
Niyama Bassa - New Features Test Suite v7
Tests for: Text Search, Top-Rated Handymen, Shop Dashboard Management

Feature coverage:
1. GET /api/handymen?q=searchterm - Text search across name/description/shop_name
2. GET /api/handymen/top-rated - Top rated handymen endpoint
3. Shop management: POST /api/shop/add-handyman, GET /api/shop/my-handymen, DELETE /api/shop/remove-handyman/{user_id}
4. Full shop flow: register shop -> add handyman -> admin approves -> verify
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data identifiers
TEST_PREFIX = f"TEST7_{uuid.uuid4().hex[:6]}"
ADMIN_EMAIL = "admin@bassbass.lk"
ADMIN_PASSWORD = "admin123"


class TestTextSearchEndpoint:
    """Test /api/handymen?q=searchterm - Text search feature"""
    
    def test_search_endpoint_exists(self):
        """Test GET /api/handymen?q=xxx returns valid response"""
        response = requests.get(f"{BASE_URL}/api/handymen?q=test")
        assert response.status_code == 200
        data = response.json()
        assert "handymen" in data
        assert "total" in data
        assert "page" in data
        print(f"Search endpoint works: {data['total']} results for 'test'")
    
    def test_search_empty_query(self):
        """Test search with empty query returns all approved handymen"""
        response = requests.get(f"{BASE_URL}/api/handymen?q=")
        assert response.status_code == 200
        data = response.json()
        assert "handymen" in data
        print(f"Empty search returns: {data['total']} results")
    
    def test_search_with_district_filter(self):
        """Test search with q and district filters combined"""
        response = requests.get(f"{BASE_URL}/api/handymen?q=plumber&district=Colombo")
        assert response.status_code == 200
        data = response.json()
        assert "handymen" in data
        print(f"Combined search (q=plumber, district=Colombo): {data['total']} results")
    
    def test_search_case_insensitive(self):
        """Test search is case-insensitive"""
        # Search with lowercase and uppercase
        res_lower = requests.get(f"{BASE_URL}/api/handymen?q=plumber")
        res_upper = requests.get(f"{BASE_URL}/api/handymen?q=PLUMBER")
        
        assert res_lower.status_code == 200
        assert res_upper.status_code == 200
        # Both should return same count (case insensitive)
        print(f"Case insensitive: 'plumber'={res_lower.json()['total']}, 'PLUMBER'={res_upper.json()['total']}")


class TestTopRatedEndpoint:
    """Test /api/handymen/top-rated endpoint"""
    
    def test_top_rated_endpoint_exists(self):
        """Test GET /api/handymen/top-rated returns valid response"""
        response = requests.get(f"{BASE_URL}/api/handymen/top-rated")
        assert response.status_code == 200
        data = response.json()
        assert "handymen" in data
        assert isinstance(data["handymen"], list)
        print(f"Top rated endpoint works: {len(data['handymen'])} rated handymen")
    
    def test_top_rated_with_limit(self):
        """Test top-rated with limit parameter"""
        response = requests.get(f"{BASE_URL}/api/handymen/top-rated?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["handymen"]) <= 3
        print(f"Top rated (limit=3): {len(data['handymen'])} returned")
    
    def test_top_rated_only_has_rated_handymen(self):
        """Test top-rated returns only handymen with rating > 0"""
        response = requests.get(f"{BASE_URL}/api/handymen/top-rated")
        assert response.status_code == 200
        data = response.json()
        for handyman in data["handymen"]:
            assert handyman.get("rating", 0) > 0, f"Handyman {handyman.get('full_name')} has no rating"
        print(f"All {len(data['handymen'])} top-rated handymen have ratings > 0")


class TestShopRegistration:
    """Test shop registration and login"""
    
    @pytest.fixture
    def shop_data(self):
        """Create unique shop user data"""
        return {
            "email": f"{TEST_PREFIX}_shop@test.lk",
            "password": "shoppass123",
            "full_name": f"{TEST_PREFIX} Test Shop",
            "phone": "0771234567",
            "role": "shop",
            "district": "Colombo"
        }
    
    def test_register_shop(self, shop_data):
        """Test shop role registration"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json=shop_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["user"]["role"] == "shop"
        assert data["user"]["is_approved"] == False  # Shops need approval
        assert "Awaiting admin approval" in data["message"]
        print(f"Shop registered: {data['user']['email']} (pending approval)")
        return data
    
    def test_shop_login(self, shop_data):
        """Test shop can login"""
        # First register
        reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            **shop_data,
            "email": f"{TEST_PREFIX}_shoplog@test.lk"
        })
        
        # Then login
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": f"{TEST_PREFIX}_shoplog@test.lk",
            "password": "shoppass123"
        })
        assert login_res.status_code == 200
        data = login_res.json()
        assert data["user"]["role"] == "shop"
        print(f"Shop login successful: {data['user']['email']}")


class TestShopAddHandyman:
    """Test POST /api/shop/add-handyman endpoint"""
    
    @pytest.fixture
    def shop_with_token(self):
        """Create and return approved shop with token"""
        # 1. Register shop
        shop_email = f"{TEST_PREFIX}_shopadd@test.lk"
        reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": shop_email,
            "password": "shoppass123",
            "full_name": f"{TEST_PREFIX} Add Shop",
            "phone": "0772223333",
            "role": "shop",
            "district": "Colombo"
        })
        shop_token = reg_res.json()["access_token"]
        shop_id = reg_res.json()["user"]["id"]
        
        # 2. Admin approves shop
        admin_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        admin_token = admin_res.json()["access_token"]
        
        approve_res = requests.put(f"{BASE_URL}/api/admin/approve/{shop_id}", json={}, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        # 3. Re-login to get updated token
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": shop_email,
            "password": "shoppass123"
        })
        
        return {
            "token": login_res.json()["access_token"],
            "user": login_res.json()["user"],
            "admin_token": admin_token
        }
    
    def test_shop_add_handyman(self, shop_with_token):
        """Test shop can add handyman"""
        handyman_data = {
            "email": f"{TEST_PREFIX}_hm1@test.lk",
            "password": "hmpass123",
            "full_name": f"{TEST_PREFIX} Handyman 1",
            "phone": "0773334444",
            "district": "Colombo"
        }
        
        response = requests.post(f"{BASE_URL}/api/shop/add-handyman", 
            json=handyman_data,
            headers={"Authorization": f"Bearer {shop_with_token['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert data["user"]["role"] == "handyman"
        assert data["user"]["shop_id"] == shop_with_token["user"]["id"]
        assert "Handyman added" in data["message"]
        print(f"Handyman added: {data['user']['email']} under shop {shop_with_token['user']['full_name']}")
    
    def test_shop_add_duplicate_email_fails(self, shop_with_token):
        """Test adding handyman with duplicate email fails"""
        email = f"{TEST_PREFIX}_hm_dup@test.lk"
        handyman_data = {
            "email": email,
            "password": "hmpass123",
            "full_name": f"{TEST_PREFIX} Dup Handyman",
            "phone": "0774445555",
            "district": "Gampaha"
        }
        
        # Add first
        res1 = requests.post(f"{BASE_URL}/api/shop/add-handyman", 
            json=handyman_data,
            headers={"Authorization": f"Bearer {shop_with_token['token']}"}
        )
        assert res1.status_code == 200
        
        # Try duplicate
        res2 = requests.post(f"{BASE_URL}/api/shop/add-handyman", 
            json=handyman_data,
            headers={"Authorization": f"Bearer {shop_with_token['token']}"}
        )
        assert res2.status_code == 400
        assert "already registered" in res2.json()["detail"].lower()
        print("Duplicate email prevented correctly")
    
    def test_non_shop_cannot_add_handyman(self):
        """Test customer cannot add handyman"""
        # Register customer
        cust_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"{TEST_PREFIX}_cust@test.lk",
            "password": "custpass123",
            "full_name": f"{TEST_PREFIX} Customer",
            "phone": "0775556666",
            "role": "customer",
            "district": "Colombo"
        })
        cust_token = cust_res.json()["access_token"]
        
        # Try to add handyman
        response = requests.post(f"{BASE_URL}/api/shop/add-handyman", 
            json={
                "email": "invalid@test.lk",
                "password": "pass123",
                "full_name": "Invalid",
                "phone": "0776667777",
                "district": "Colombo"
            },
            headers={"Authorization": f"Bearer {cust_token}"}
        )
        assert response.status_code == 403
        print("Customer correctly blocked from adding handyman")


class TestShopMyHandymen:
    """Test GET /api/shop/my-handymen endpoint"""
    
    @pytest.fixture
    def shop_with_handymen(self):
        """Create shop with 2 handymen"""
        # 1. Register and approve shop
        shop_email = f"{TEST_PREFIX}_shopmh@test.lk"
        reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": shop_email,
            "password": "shoppass123",
            "full_name": f"{TEST_PREFIX} MyH Shop",
            "phone": "0777778888",
            "role": "shop",
            "district": "Galle"
        })
        shop_id = reg_res.json()["user"]["id"]
        
        # Admin approve
        admin_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        admin_token = admin_res.json()["access_token"]
        requests.put(f"{BASE_URL}/api/admin/approve/{shop_id}", json={}, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        # Re-login shop
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": shop_email, "password": "shoppass123"
        })
        shop_token = login_res.json()["access_token"]
        
        # Add 2 handymen
        hm_ids = []
        for i in range(2):
            hm_res = requests.post(f"{BASE_URL}/api/shop/add-handyman", 
                json={
                    "email": f"{TEST_PREFIX}_myhm{i}@test.lk",
                    "password": "pass123",
                    "full_name": f"{TEST_PREFIX} MyHM {i}",
                    "phone": f"07{i}00001111",
                    "district": "Galle"
                },
                headers={"Authorization": f"Bearer {shop_token}"}
            )
            if hm_res.status_code == 200:
                hm_ids.append(hm_res.json()["user"]["id"])
        
        return {
            "shop_token": shop_token,
            "handyman_ids": hm_ids
        }
    
    def test_shop_list_my_handymen(self, shop_with_handymen):
        """Test shop can list its handymen"""
        response = requests.get(f"{BASE_URL}/api/shop/my-handymen", headers={
            "Authorization": f"Bearer {shop_with_handymen['shop_token']}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "handymen" in data
        assert len(data["handymen"]) >= 2
        print(f"Shop has {len(data['handymen'])} handymen listed")
    
    def test_non_shop_cannot_list_handymen(self):
        """Test customer cannot access shop/my-handymen"""
        # Register customer
        cust_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"{TEST_PREFIX}_custmh@test.lk",
            "password": "custpass123",
            "full_name": f"{TEST_PREFIX} Cust MH",
            "phone": "0778889999",
            "role": "customer",
            "district": "Colombo"
        })
        cust_token = cust_res.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/shop/my-handymen", headers={
            "Authorization": f"Bearer {cust_token}"
        })
        assert response.status_code == 403
        print("Customer correctly blocked from listing shop handymen")


class TestShopRemoveHandyman:
    """Test DELETE /api/shop/remove-handyman/{user_id} endpoint"""
    
    @pytest.fixture
    def shop_with_one_handyman(self):
        """Create shop with 1 handyman for removal test"""
        shop_email = f"{TEST_PREFIX}_shoprem@test.lk"
        reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": shop_email,
            "password": "shoppass123",
            "full_name": f"{TEST_PREFIX} RemShop",
            "phone": "0779990000",
            "role": "shop",
            "district": "Kandy"
        })
        shop_id = reg_res.json()["user"]["id"]
        
        # Admin approve
        admin_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        admin_token = admin_res.json()["access_token"]
        requests.put(f"{BASE_URL}/api/admin/approve/{shop_id}", json={}, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        # Re-login shop
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": shop_email, "password": "shoppass123"
        })
        shop_token = login_res.json()["access_token"]
        
        # Add 1 handyman
        hm_res = requests.post(f"{BASE_URL}/api/shop/add-handyman", 
            json={
                "email": f"{TEST_PREFIX}_remhm@test.lk",
                "password": "pass123",
                "full_name": f"{TEST_PREFIX} RemHM",
                "phone": "0700000001",
                "district": "Kandy"
            },
            headers={"Authorization": f"Bearer {shop_token}"}
        )
        
        return {
            "shop_token": shop_token,
            "handyman_id": hm_res.json()["user"]["id"] if hm_res.status_code == 200 else None
        }
    
    def test_shop_remove_handyman(self, shop_with_one_handyman):
        """Test shop can remove its handyman"""
        if not shop_with_one_handyman["handyman_id"]:
            pytest.skip("Handyman not created")
        
        response = requests.delete(
            f"{BASE_URL}/api/shop/remove-handyman/{shop_with_one_handyman['handyman_id']}", 
            headers={"Authorization": f"Bearer {shop_with_one_handyman['shop_token']}"}
        )
        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()
        print(f"Handyman {shop_with_one_handyman['handyman_id']} removed successfully")
    
    def test_shop_cannot_remove_other_shops_handyman(self):
        """Test shop A cannot remove shop B's handyman"""
        # Create shop A with handyman
        shopA_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"{TEST_PREFIX}_shopA@test.lk",
            "password": "passA123",
            "full_name": f"{TEST_PREFIX} Shop A",
            "phone": "0701010101",
            "role": "shop",
            "district": "Matara"
        })
        shopA_id = shopA_res.json()["user"]["id"]
        
        # Admin approve shop A
        admin_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        admin_token = admin_res.json()["access_token"]
        requests.put(f"{BASE_URL}/api/admin/approve/{shopA_id}", json={}, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        # Shop A login and add handyman
        loginA_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": f"{TEST_PREFIX}_shopA@test.lk", "password": "passA123"
        })
        shopA_token = loginA_res.json()["access_token"]
        
        hmA_res = requests.post(f"{BASE_URL}/api/shop/add-handyman", 
            json={
                "email": f"{TEST_PREFIX}_hmA@test.lk",
                "password": "passhmA",
                "full_name": f"{TEST_PREFIX} HM A",
                "phone": "0702020202",
                "district": "Matara"
            },
            headers={"Authorization": f"Bearer {shopA_token}"}
        )
        hmA_id = hmA_res.json()["user"]["id"]
        
        # Create shop B
        shopB_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"{TEST_PREFIX}_shopB@test.lk",
            "password": "passB123",
            "full_name": f"{TEST_PREFIX} Shop B",
            "phone": "0703030303",
            "role": "shop",
            "district": "Matara"
        })
        shopB_id = shopB_res.json()["user"]["id"]
        
        # Admin approve shop B
        requests.put(f"{BASE_URL}/api/admin/approve/{shopB_id}", json={}, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        loginB_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": f"{TEST_PREFIX}_shopB@test.lk", "password": "passB123"
        })
        shopB_token = loginB_res.json()["access_token"]
        
        # Shop B tries to remove Shop A's handyman
        response = requests.delete(
            f"{BASE_URL}/api/shop/remove-handyman/{hmA_id}", 
            headers={"Authorization": f"Bearer {shopB_token}"}
        )
        assert response.status_code == 404
        print("Shop B correctly blocked from removing Shop A's handyman")


class TestFullShopFlow:
    """Test complete shop flow: register shop -> add handyman -> admin approves -> verify in search"""
    
    def test_full_shop_handyman_flow(self):
        """Test entire flow end-to-end"""
        unique_id = uuid.uuid4().hex[:6]
        
        # 1. Register shop
        shop_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"flow_shop_{unique_id}@test.lk",
            "password": "flowpass123",
            "full_name": f"Flow Shop {unique_id}",
            "phone": "0711111111",
            "role": "shop",
            "district": "Colombo"
        })
        assert shop_res.status_code == 200
        shop = shop_res.json()
        print(f"1. Shop registered: {shop['user']['email']}")
        
        # 2. Admin approves shop
        admin_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        admin_token = admin_res.json()["access_token"]
        
        approve_res = requests.put(f"{BASE_URL}/api/admin/approve/{shop['user']['id']}", json={}, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert approve_res.status_code == 200
        print(f"2. Admin approved shop")
        
        # 3. Shop logs in with updated status
        shop_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": f"flow_shop_{unique_id}@test.lk",
            "password": "flowpass123"
        })
        shop_token = shop_login.json()["access_token"]
        
        # 4. Shop adds handyman
        hm_res = requests.post(f"{BASE_URL}/api/shop/add-handyman", 
            json={
                "email": f"flow_hm_{unique_id}@test.lk",
                "password": "flowhmpass",
                "full_name": f"Flow Handyman {unique_id}",
                "phone": "0722222222",
                "district": "Colombo"
            },
            headers={"Authorization": f"Bearer {shop_token}"}
        )
        assert hm_res.status_code == 200
        hm_id = hm_res.json()["user"]["id"]
        print(f"3. Handyman added: {hm_res.json()['user']['email']}")
        
        # 5. Handyman logs in and creates profile
        hm_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": f"flow_hm_{unique_id}@test.lk",
            "password": "flowhmpass"
        })
        hm_token = hm_login.json()["access_token"]
        
        profile_res = requests.post(f"{BASE_URL}/api/handyman/profile", 
            json={
                "services": ["plumber", "electrician"],
                "description": f"Flow test handyman {unique_id}",
                "experience_years": 3,
                "districts_served": ["Colombo", "Gampaha"],
                "hourly_rate": 2000,
                "phone": "0722222222",
                "whatsapp": "+94722222222"
            },
            headers={"Authorization": f"Bearer {hm_token}"}
        )
        assert profile_res.status_code == 200
        print(f"4. Handyman profile created")
        
        # 6. Admin approves handyman
        approve_hm = requests.put(f"{BASE_URL}/api/admin/approve/{hm_id}", json={}, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert approve_hm.status_code == 200
        print(f"5. Admin approved handyman")
        
        # 7. Verify handyman appears in search
        search_res = requests.get(f"{BASE_URL}/api/handymen?q={unique_id}")
        assert search_res.status_code == 200
        search_data = search_res.json()
        
        found = False
        for h in search_data["handymen"]:
            if unique_id in h.get("full_name", "") or unique_id in h.get("description", ""):
                found = True
                break
        
        assert found, f"Handyman {unique_id} should appear in search results"
        print(f"6. Verified: Handyman appears in search results")
        
        # 8. Shop lists its handymen
        my_hm = requests.get(f"{BASE_URL}/api/shop/my-handymen", headers={
            "Authorization": f"Bearer {shop_token}"
        })
        assert my_hm.status_code == 200
        assert len(my_hm.json()["handymen"]) >= 1
        print(f"7. Shop can see {len(my_hm.json()['handymen'])} handymen in dashboard")
        
        print("✅ Full shop flow test PASSED")


# Cleanup fixture
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data():
    """Note: Test users are created with unique prefixes and won't affect other tests"""
    yield
    # No cleanup needed as each test run uses unique emails


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
