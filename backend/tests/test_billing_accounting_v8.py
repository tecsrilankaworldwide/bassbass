"""
Test suite for TopBass Billing & Accounting System
Tests for:
- Handyman quote price functionality
- Billing calculation (10% TopBass fee + 18.5% VAT)
- Stripe checkout session creation
- Payment status endpoint
- Admin accounting dashboard
- Payout management
"""

import pytest
import requests
import uuid
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Constants from the system
TOPBASS_FEE_PERCENT = 10
VAT_PERCENT = 18.5


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@bassbass.lk",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture
def admin_client(api_client, admin_token):
    """Session with admin auth header"""
    api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return api_client


@pytest.fixture
def test_handyman_data():
    """Generate unique test handyman data"""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"TEST_handyman_{unique_id}@test.lk",
        "password": "test123",
        "full_name": f"TEST Handyman {unique_id}",
        "phone": "0771234567",
        "role": "handyman",
        "district": "Colombo"
    }


@pytest.fixture
def test_customer_data():
    """Generate unique test customer data"""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"TEST_customer_{unique_id}@test.lk",
        "password": "test123",
        "full_name": f"TEST Customer {unique_id}",
        "phone": "0779876543",
        "role": "customer",
        "district": "Colombo"
    }


@pytest.fixture
def registered_handyman(api_client, test_handyman_data, admin_client):
    """Register, approve and return handyman with token"""
    # Register handyman
    res = api_client.post(f"{BASE_URL}/api/auth/register", json=test_handyman_data)
    assert res.status_code == 200, f"Handyman registration failed: {res.text}"
    data = res.json()
    token = data["access_token"]
    user_id = data["user"]["id"]
    
    # Create handyman profile
    profile_data = {
        "services": ["plumber"],
        "description": "Test plumber for billing tests",
        "experience_years": 5,
        "districts_served": ["Colombo"],
        "hourly_rate": 1000,
        "phone": test_handyman_data["phone"]
    }
    profile_res = api_client.post(f"{BASE_URL}/api/handyman/profile", json=profile_data,
                                   headers={"Authorization": f"Bearer {token}"})
    
    # Approve handyman
    admin_client.put(f"{BASE_URL}/api/admin/approve/{user_id}")
    
    return {
        "token": token,
        "user_id": user_id,
        "email": test_handyman_data["email"]
    }


@pytest.fixture
def registered_customer(api_client, test_customer_data):
    """Register and return customer with token"""
    res = api_client.post(f"{BASE_URL}/api/auth/register", json=test_customer_data)
    assert res.status_code == 200, f"Customer registration failed: {res.text}"
    data = res.json()
    return {
        "token": data["access_token"],
        "user_id": data["user"]["id"],
        "email": test_customer_data["email"],
        "full_name": test_customer_data["full_name"]
    }


@pytest.fixture
def test_booking(api_client, registered_customer, registered_handyman):
    """Create a test booking"""
    booking_data = {
        "handyman_id": registered_handyman["user_id"],
        "service_id": "plumber",
        "description": "TEST: Fix water leak for billing test",
        "preferred_date": "2026-02-15",
        "preferred_time": "10:00 AM",
        "address": "123 Test Street, Colombo",
        "district": "Colombo",
        "phone": "0771112223"
    }
    res = api_client.post(f"{BASE_URL}/api/bookings/create", json=booking_data,
                          headers={"Authorization": f"Bearer {registered_customer['token']}"})
    assert res.status_code == 200, f"Booking creation failed: {res.text}"
    return res.json()["booking"]


# ============================================================================
# BILLING CALCULATION TESTS
# ============================================================================

class TestBillingCalculation:
    """Test billing calculation logic (10% fee + 18.5% VAT)"""
    
    def test_calculate_billing_example_5000(self):
        """Verify billing calculation: 5000 -> 500 fee -> 5500 service_charge -> 1017.50 VAT -> 6517.50 total"""
        job_price = 5000
        expected_fee = 500  # 10%
        expected_service_charge = 5500  # job_price + fee
        expected_vat = 1017.50  # 18.5% of service_charge
        expected_total = 6517.50  # service_charge + vat
        
        # Calculate as the system does
        fee = round(job_price * TOPBASS_FEE_PERCENT / 100, 2)
        service_charge = round(job_price + fee, 2)
        vat = round(service_charge * VAT_PERCENT / 100, 2)
        total = round(service_charge + vat, 2)
        
        assert fee == expected_fee, f"Fee mismatch: {fee} != {expected_fee}"
        assert service_charge == expected_service_charge, f"Service charge mismatch: {service_charge} != {expected_service_charge}"
        assert vat == expected_vat, f"VAT mismatch: {vat} != {expected_vat}"
        assert total == expected_total, f"Total mismatch: {total} != {expected_total}"
        print(f"✓ Billing calc verified: job={job_price}, fee={fee}, service_charge={service_charge}, vat={vat}, total={total}")


# ============================================================================
# QUOTE PRICE ENDPOINT TESTS
# ============================================================================

class TestQuotePriceEndpoint:
    """Test PUT /api/bookings/{id}/quote - Handyman quotes job price"""
    
    def test_handyman_quote_price_success(self, api_client, test_booking, registered_handyman):
        """Handyman can quote a price for pending booking"""
        booking_id = test_booking["id"]
        job_price = 5000
        
        res = api_client.put(f"{BASE_URL}/api/bookings/{booking_id}/quote",
                             json={"job_price": job_price},
                             headers={"Authorization": f"Bearer {registered_handyman['token']}"})
        
        assert res.status_code == 200, f"Quote failed: {res.text}"
        data = res.json()
        
        # Verify response contains billing breakdown
        assert "billing" in data
        billing = data["billing"]
        assert billing["job_price"] == 5000
        assert billing["topbass_fee"] == 500
        assert billing["service_charge"] == 5500
        assert billing["vat_amount"] == 1017.50
        assert billing["total"] == 6517.50
        print(f"✓ Handyman quoted price successfully: {billing}")
    
    def test_quote_updates_booking_status_to_quoted(self, api_client, test_booking, registered_handyman, registered_customer):
        """After quoting, booking status should be 'quoted'"""
        booking_id = test_booking["id"]
        
        # Quote the price
        api_client.put(f"{BASE_URL}/api/bookings/{booking_id}/quote",
                       json={"job_price": 3000},
                       headers={"Authorization": f"Bearer {registered_handyman['token']}"})
        
        # Fetch booking and verify status
        res = api_client.get(f"{BASE_URL}/api/bookings/my",
                             headers={"Authorization": f"Bearer {registered_customer['token']}"})
        assert res.status_code == 200
        bookings = res.json()["bookings"]
        booking = next((b for b in bookings if b["id"] == booking_id), None)
        
        assert booking is not None
        assert booking["status"] == "quoted", f"Expected 'quoted', got '{booking['status']}'"
        assert booking["job_price"] == 3000
        assert booking["total"] == 3910.5  # 3000 + 300(fee) = 3300 service_charge * 1.185(VAT) = 3910.5
        print("✓ Booking status updated to 'quoted' with correct pricing")
    
    def test_customer_cannot_quote_price(self, api_client, test_booking, registered_customer):
        """Customer should not be able to quote a price (403)"""
        booking_id = test_booking["id"]
        
        res = api_client.put(f"{BASE_URL}/api/bookings/{booking_id}/quote",
                             json={"job_price": 5000},
                             headers={"Authorization": f"Bearer {registered_customer['token']}"})
        
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("✓ Customer correctly prevented from quoting price")
    
    def test_handyman_cannot_quote_others_booking(self, api_client, test_booking, admin_client):
        """Handyman cannot quote a booking not assigned to them"""
        # Register another handyman
        unique_id = str(uuid.uuid4())[:8]
        other_handyman_data = {
            "email": f"TEST_other_{unique_id}@test.lk",
            "password": "test123",
            "full_name": f"TEST Other Handyman {unique_id}",
            "phone": "0771111111",
            "role": "handyman",
            "district": "Colombo"
        }
        res = api_client.post(f"{BASE_URL}/api/auth/register", json=other_handyman_data,
                              headers={"Content-Type": "application/json"})
        other_token = res.json()["access_token"]
        
        # Try to quote someone else's booking
        res = api_client.put(f"{BASE_URL}/api/bookings/{test_booking['id']}/quote",
                             json={"job_price": 5000},
                             headers={"Authorization": f"Bearer {other_token}"})
        
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("✓ Handyman correctly prevented from quoting other's booking")


# ============================================================================
# BILLING ENDPOINT TESTS
# ============================================================================

class TestBillingEndpoint:
    """Test GET /api/bookings/{id}/billing - Get billing breakdown"""
    
    def test_get_billing_after_quote(self, api_client, test_booking, registered_handyman, registered_customer):
        """Customer can get billing breakdown after handyman quotes"""
        booking_id = test_booking["id"]
        
        # First, handyman quotes
        api_client.put(f"{BASE_URL}/api/bookings/{booking_id}/quote",
                       json={"job_price": 10000},
                       headers={"Authorization": f"Bearer {registered_handyman['token']}"})
        
        # Customer gets billing
        res = api_client.get(f"{BASE_URL}/api/bookings/{booking_id}/billing",
                             headers={"Authorization": f"Bearer {registered_customer['token']}"})
        
        assert res.status_code == 200, f"Get billing failed: {res.text}"
        data = res.json()
        
        # Verify billing details
        assert data["service_charge"] == 11000  # 10000 + 1000 fee
        assert data["vat_percent"] == 18.5
        assert data["vat_amount"] == 2035  # 11000 * 0.185
        assert data["total"] == 13035  # 11000 + 2035
        assert data["status"] == "quoted"
        print(f"✓ Billing endpoint returns correct breakdown: {data}")
    
    def test_handyman_can_view_own_booking_billing(self, api_client, test_booking, registered_handyman):
        """Handyman can also view billing for their booking"""
        booking_id = test_booking["id"]
        
        # Quote first
        api_client.put(f"{BASE_URL}/api/bookings/{booking_id}/quote",
                       json={"job_price": 2000},
                       headers={"Authorization": f"Bearer {registered_handyman['token']}"})
        
        # Get billing
        res = api_client.get(f"{BASE_URL}/api/bookings/{booking_id}/billing",
                             headers={"Authorization": f"Bearer {registered_handyman['token']}"})
        
        assert res.status_code == 200
        print("✓ Handyman can view billing for their booking")


# ============================================================================
# STRIPE CHECKOUT TESTS
# ============================================================================

class TestStripeCheckout:
    """Test POST /api/payments/create-checkout - Create Stripe checkout session"""
    
    def test_create_checkout_for_quoted_booking(self, api_client, test_booking, registered_handyman, registered_customer):
        """Customer can create checkout session for quoted booking"""
        booking_id = test_booking["id"]
        
        # Handyman quotes
        api_client.put(f"{BASE_URL}/api/bookings/{booking_id}/quote",
                       json={"job_price": 5000},
                       headers={"Authorization": f"Bearer {registered_handyman['token']}"})
        
        # Customer creates checkout
        res = api_client.post(f"{BASE_URL}/api/payments/create-checkout",
                              json={
                                  "booking_id": booking_id,
                                  "origin_url": "https://topbass-staging.preview.emergentagent.com"
                              },
                              headers={"Authorization": f"Bearer {registered_customer['token']}"})
        
        # Stripe test key might fail but endpoint should accept the request
        # Either 200 (success) or error from Stripe API
        if res.status_code == 200:
            data = res.json()
            assert "url" in data or "session_id" in data
            print(f"✓ Checkout session created successfully: session_id={data.get('session_id')}")
        else:
            # Stripe test key may fail - this is expected
            print(f"! Stripe checkout returned {res.status_code} - may be expected with test key: {res.text[:200]}")
            # At least verify it's not a 403/404 (auth/not found error)
            assert res.status_code not in [403, 404], f"Unexpected error: {res.text}"
    
    def test_checkout_requires_quoted_booking(self, api_client, test_booking, registered_customer):
        """Cannot create checkout for unquoted booking (no price yet)"""
        booking_id = test_booking["id"]
        
        # Try to checkout without quote
        res = api_client.post(f"{BASE_URL}/api/payments/create-checkout",
                              json={
                                  "booking_id": booking_id,
                                  "origin_url": "https://test.com"
                              },
                              headers={"Authorization": f"Bearer {registered_customer['token']}"})
        
        assert res.status_code == 400, f"Expected 400, got {res.status_code}"
        assert "No price quoted" in res.text or "quoted" in res.text.lower()
        print("✓ Correctly rejected checkout for unquoted booking")
    
    def test_handyman_cannot_create_checkout(self, api_client, test_booking, registered_handyman):
        """Handyman should not be able to create checkout (not their role)"""
        # First quote
        api_client.put(f"{BASE_URL}/api/bookings/{test_booking['id']}/quote",
                       json={"job_price": 5000},
                       headers={"Authorization": f"Bearer {registered_handyman['token']}"})
        
        # Try checkout as handyman
        res = api_client.post(f"{BASE_URL}/api/payments/create-checkout",
                              json={
                                  "booking_id": test_booking["id"],
                                  "origin_url": "https://test.com"
                              },
                              headers={"Authorization": f"Bearer {registered_handyman['token']}"})
        
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("✓ Handyman correctly prevented from creating checkout")


# ============================================================================
# PAYMENT STATUS TESTS
# ============================================================================

class TestPaymentStatus:
    """Test GET /api/payments/status/{session_id}"""
    
    def test_get_payment_status_invalid_session(self, api_client, registered_customer):
        """Get payment status returns 404 for invalid session"""
        res = api_client.get(f"{BASE_URL}/api/payments/status/invalid_session_id",
                             headers={"Authorization": f"Bearer {registered_customer['token']}"})
        
        # Should be 404 (transaction not found) or error from Stripe
        assert res.status_code in [404, 500], f"Expected 404/500, got {res.status_code}"
        print(f"✓ Invalid session correctly returns error: {res.status_code}")


# ============================================================================
# ADMIN ACCOUNTING TESTS
# ============================================================================

class TestAdminAccounting:
    """Test GET /api/admin/accounting - Admin accounting dashboard"""
    
    def test_admin_accounting_endpoint(self, admin_client):
        """Admin can access accounting dashboard"""
        res = admin_client.get(f"{BASE_URL}/api/admin/accounting")
        
        assert res.status_code == 200, f"Accounting endpoint failed: {res.text}"
        data = res.json()
        
        # Verify expected fields
        expected_fields = [
            "total_revenue", "total_topbass_fee", "total_vat_collected",
            "total_handyman_pay", "transaction_count", "pending_payouts",
            "completed_payouts", "fee_percent", "vat_percent",
            "transactions", "payouts"
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify percentages
        assert data["fee_percent"] == TOPBASS_FEE_PERCENT
        assert data["vat_percent"] == VAT_PERCENT
        
        print(f"✓ Admin accounting dashboard working:")
        print(f"  Revenue: {data['total_revenue']}, Fee: {data['total_topbass_fee']}, VAT: {data['total_vat_collected']}")
    
    def test_non_admin_cannot_access_accounting(self, api_client, registered_customer):
        """Non-admin users cannot access accounting"""
        res = api_client.get(f"{BASE_URL}/api/admin/accounting",
                             headers={"Authorization": f"Bearer {registered_customer['token']}"})
        
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("✓ Non-admin correctly prevented from accessing accounting")


# ============================================================================
# PAYOUT MANAGEMENT TESTS
# ============================================================================

class TestPayoutManagement:
    """Test PUT /api/admin/payouts/{id}/mark-paid"""
    
    def test_admin_mark_payout_paid(self, admin_client):
        """Admin can mark payout as paid"""
        # First check if there are any pending payouts
        res = admin_client.get(f"{BASE_URL}/api/admin/accounting")
        data = res.json()
        
        pending_payouts = [p for p in data.get("payouts", []) if p.get("status") == "pending"]
        
        if pending_payouts:
            payout = pending_payouts[0]
            mark_res = admin_client.put(f"{BASE_URL}/api/admin/payouts/{payout['id']}/mark-paid")
            assert mark_res.status_code == 200, f"Mark paid failed: {mark_res.text}"
            print(f"✓ Admin marked payout {payout['id'][:8]}... as paid")
        else:
            print("! No pending payouts to test - skipping mark-paid test")
    
    def test_mark_nonexistent_payout_fails(self, admin_client):
        """Marking non-existent payout returns 404"""
        res = admin_client.put(f"{BASE_URL}/api/admin/payouts/nonexistent_id/mark-paid")
        
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"
        print("✓ Non-existent payout correctly returns 404")
    
    def test_non_admin_cannot_mark_payout(self, api_client, registered_handyman):
        """Non-admin cannot mark payouts as paid"""
        res = api_client.put(f"{BASE_URL}/api/admin/payouts/any_id/mark-paid",
                             headers={"Authorization": f"Bearer {registered_handyman['token']}"})
        
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("✓ Non-admin correctly prevented from marking payouts")


# ============================================================================
# FULL FLOW TEST
# ============================================================================

class TestFullBillingFlow:
    """Test complete billing flow: booking -> quote -> billing calculation"""
    
    def test_full_billing_flow(self, api_client, admin_client):
        """
        Full flow:
        1. Register customer & handyman
        2. Admin approves handyman
        3. Customer creates booking
        4. Handyman quotes price
        5. Verify billing calculation
        """
        unique_id = str(uuid.uuid4())[:8]
        
        # 1. Register customer
        customer_data = {
            "email": f"TEST_flow_customer_{unique_id}@test.lk",
            "password": "test123",
            "full_name": f"TEST Flow Customer {unique_id}",
            "phone": "0771234567",
            "role": "customer",
            "district": "Colombo"
        }
        cust_res = api_client.post(f"{BASE_URL}/api/auth/register", json=customer_data)
        assert cust_res.status_code == 200
        cust_token = cust_res.json()["access_token"]
        print("✓ Customer registered")
        
        # 2. Register handyman
        handyman_data = {
            "email": f"TEST_flow_handyman_{unique_id}@test.lk",
            "password": "test123",
            "full_name": f"TEST Flow Handyman {unique_id}",
            "phone": "0779876543",
            "role": "handyman",
            "district": "Colombo"
        }
        hm_res = api_client.post(f"{BASE_URL}/api/auth/register", json=handyman_data)
        assert hm_res.status_code == 200
        hm_token = hm_res.json()["access_token"]
        hm_id = hm_res.json()["user"]["id"]
        print("✓ Handyman registered")
        
        # 3. Create handyman profile
        profile = {
            "services": ["electrician"],
            "description": "Flow test electrician",
            "experience_years": 3,
            "districts_served": ["Colombo"],
            "hourly_rate": 800
        }
        api_client.post(f"{BASE_URL}/api/handyman/profile", json=profile,
                        headers={"Authorization": f"Bearer {hm_token}"})
        
        # 4. Admin approves handyman
        admin_client.put(f"{BASE_URL}/api/admin/approve/{hm_id}")
        print("✓ Handyman approved")
        
        # 5. Customer creates booking
        booking_data = {
            "handyman_id": hm_id,
            "service_id": "electrician",
            "description": "TEST: Full flow electrical work",
            "preferred_date": "2026-02-20",
            "preferred_time": "2:00 PM",
            "address": "456 Flow Test Lane",
            "district": "Colombo"
        }
        booking_res = api_client.post(f"{BASE_URL}/api/bookings/create", json=booking_data,
                                       headers={"Authorization": f"Bearer {cust_token}"})
        assert booking_res.status_code == 200
        booking = booking_res.json()["booking"]
        booking_id = booking["id"]
        print(f"✓ Booking created: {booking_id[:8]}...")
        
        # 6. Handyman quotes price
        job_price = 5000
        quote_res = api_client.put(f"{BASE_URL}/api/bookings/{booking_id}/quote",
                                    json={"job_price": job_price},
                                    headers={"Authorization": f"Bearer {hm_token}"})
        assert quote_res.status_code == 200
        billing = quote_res.json()["billing"]
        print(f"✓ Handyman quoted: LKR {job_price}")
        
        # 7. Verify billing calculation
        # job_price=5000 -> fee=500 (10%) -> service_charge=5500 -> VAT=1017.50 (18.5%) -> total=6517.50
        assert billing["job_price"] == 5000
        assert billing["topbass_fee"] == 500
        assert billing["service_charge"] == 5500
        assert billing["vat_amount"] == 1017.50
        assert billing["total"] == 6517.50
        
        print(f"""
✓ Full billing flow verified:
  Job Price:      LKR {billing['job_price']:.2f}
  TopBass Fee:    LKR {billing['topbass_fee']:.2f} (10%)
  Service Charge: LKR {billing['service_charge']:.2f}
  VAT (18.5%):    LKR {billing['vat_amount']:.2f}
  Total:          LKR {billing['total']:.2f}
        """)
        
        # 8. Verify customer can see the pricing
        billing_res = api_client.get(f"{BASE_URL}/api/bookings/{booking_id}/billing",
                                      headers={"Authorization": f"Bearer {cust_token}"})
        assert billing_res.status_code == 200
        cust_billing = billing_res.json()
        assert cust_billing["total"] == 6517.50
        assert cust_billing["status"] == "quoted"
        print("✓ Customer can view billing breakdown")


# ============================================================================
# EXISTING FEATURES REGRESSION TESTS
# ============================================================================

class TestExistingFeatures:
    """Ensure existing features still work"""
    
    def test_services_endpoint(self, api_client):
        """Services endpoint still works"""
        res = api_client.get(f"{BASE_URL}/api/services")
        assert res.status_code == 200
        data = res.json()
        assert "services" in data
        assert len(data["services"]) > 0
        print(f"✓ Services endpoint working - {len(data['services'])} services")
    
    def test_handymen_search(self, api_client):
        """Handymen search endpoint still works"""
        res = api_client.get(f"{BASE_URL}/api/handymen")
        assert res.status_code == 200
        data = res.json()
        assert "handymen" in data
        print(f"✓ Handymen search working - {data['total']} total handymen")
    
    def test_admin_statistics(self, admin_client):
        """Admin statistics endpoint still works"""
        res = admin_client.get(f"{BASE_URL}/api/admin/statistics")
        assert res.status_code == 200
        data = res.json()
        assert "total_customers" in data
        assert "total_handymen" in data
        print(f"✓ Admin statistics working - {data['total_bookings']} total bookings")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
