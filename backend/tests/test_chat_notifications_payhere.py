"""
Test Chat, Notifications, and PayHere Payment features for TopBass marketplace
Tests:
- Chat endpoints: POST /api/chat/send, GET /api/chat/messages/{id}, GET /api/chat/conversations
- Notifications: GET /api/notifications, PUT /api/notifications/read-all, PUT /api/notifications/{id}/read
- PayHere: POST /api/payments/payhere-checkout (expected 503 - not configured)
- Auto-notification creation on booking events
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

class TestChatNotificationsPayHere:
    """Tests for Chat, Notifications, and PayHere features"""
    
    @pytest.fixture(scope="class")
    def customer_credentials(self):
        """Create a test customer for chat tests"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"TEST_chatcust_{unique_id}@test.com"
        password = "testpass123"
        
        # Register
        res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "full_name": f"Test Chat Customer {unique_id}",
            "phone": "0771234567",
            "role": "customer",
            "district": "Colombo"
        })
        assert res.status_code == 200, f"Customer registration failed: {res.text}"
        data = res.json()
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "email": email,
            "password": password,
            "full_name": data["user"]["full_name"]
        }
    
    @pytest.fixture(scope="class")
    def handyman_credentials(self):
        """Create and approve a test handyman for chat tests"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"TEST_chathandyman_{unique_id}@test.com"
        password = "testpass123"
        
        # Register
        res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "full_name": f"Test Chat Handyman {unique_id}",
            "phone": "0779876543",
            "role": "handyman",
            "district": "Colombo"
        })
        assert res.status_code == 200, f"Handyman registration failed: {res.text}"
        data = res.json()
        handyman_token = data["access_token"]
        handyman_id = data["user"]["id"]
        
        # Create profile
        requests.post(f"{BASE_URL}/api/handyman/profile", json={
            "services": ["plumber", "electrician"],
            "description": "Test handyman for chat tests",
            "experience_years": 5,
            "districts_served": ["Colombo", "Gampaha"],
            "hourly_rate": 500,
            "phone": "0779876543",
            "whatsapp": "0779876543"
        }, headers={"Authorization": f"Bearer {handyman_token}"})
        
        # Admin approve
        admin_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@bassbass.lk",
            "password": "admin123"
        })
        admin_token = admin_res.json()["access_token"]
        requests.put(f"{BASE_URL}/api/admin/approve/{handyman_id}", 
                    headers={"Authorization": f"Bearer {admin_token}"})
        
        return {
            "token": handyman_token,
            "user_id": handyman_id,
            "email": email,
            "password": password,
            "full_name": data["user"]["full_name"]
        }
    
    @pytest.fixture(scope="class")
    def booking_with_quote(self, customer_credentials, handyman_credentials):
        """Create a booking and quote it so chat can work"""
        customer_token = customer_credentials["token"]
        handyman_token = handyman_credentials["token"]
        handyman_id = handyman_credentials["user_id"]
        
        # Create booking
        booking_res = requests.post(f"{BASE_URL}/api/bookings/create", json={
            "handyman_id": handyman_id,
            "service_id": "plumber",
            "description": "Test chat booking - fix water heater",
            "preferred_date": "2026-02-15",
            "preferred_time": "10:00",
            "address": "123 Test Street, Colombo",
            "district": "Colombo",
            "phone": "0771234567"
        }, headers={"Authorization": f"Bearer {customer_token}"})
        assert booking_res.status_code == 200, f"Booking failed: {booking_res.text}"
        booking_id = booking_res.json()["booking"]["id"]
        
        # Handyman quotes the booking
        quote_res = requests.put(f"{BASE_URL}/api/bookings/{booking_id}/quote", json={
            "job_price": 3000
        }, headers={"Authorization": f"Bearer {handyman_token}"})
        assert quote_res.status_code == 200, f"Quote failed: {quote_res.text}"
        
        return {
            "booking_id": booking_id,
            "customer_token": customer_token,
            "handyman_token": handyman_token,
            "customer_id": customer_credentials["user_id"],
            "handyman_id": handyman_id
        }

    # ============================
    # CHAT TESTS
    # ============================
    
    def test_send_chat_message_customer(self, booking_with_quote):
        """Customer can send a chat message"""
        res = requests.post(f"{BASE_URL}/api/chat/send", json={
            "booking_id": booking_with_quote["booking_id"],
            "message": "Hi, when can you come to fix this?"
        }, headers={"Authorization": f"Bearer {booking_with_quote['customer_token']}"})
        
        assert res.status_code == 200, f"Send message failed: {res.text}"
        data = res.json()
        assert "message" in data
        assert data["message"]["message"] == "Hi, when can you come to fix this?"
        assert data["message"]["sender_id"] == booking_with_quote["customer_id"]
        print("✓ Customer sent chat message successfully")
    
    def test_send_chat_message_handyman(self, booking_with_quote):
        """Handyman can send a chat message"""
        res = requests.post(f"{BASE_URL}/api/chat/send", json={
            "booking_id": booking_with_quote["booking_id"],
            "message": "I can come tomorrow at 10am. Does that work?"
        }, headers={"Authorization": f"Bearer {booking_with_quote['handyman_token']}"})
        
        assert res.status_code == 200, f"Send message failed: {res.text}"
        data = res.json()
        assert data["message"]["sender_id"] == booking_with_quote["handyman_id"]
        print("✓ Handyman sent chat message successfully")
    
    def test_get_chat_messages(self, booking_with_quote):
        """Get chat messages for a booking"""
        res = requests.get(f"{BASE_URL}/api/chat/messages/{booking_with_quote['booking_id']}", 
                          headers={"Authorization": f"Bearer {booking_with_quote['customer_token']}"})
        
        assert res.status_code == 200, f"Get messages failed: {res.text}"
        data = res.json()
        assert "messages" in data
        assert "other_user" in data
        assert "booking" in data
        assert len(data["messages"]) >= 2  # At least customer + handyman messages
        print(f"✓ Got {len(data['messages'])} chat messages")
    
    def test_get_chat_messages_unauthorized(self, booking_with_quote, customer_credentials):
        """User not part of booking cannot get messages"""
        # Create another customer
        unique_id = str(uuid.uuid4())[:8]
        res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_other_{unique_id}@test.com",
            "password": "testpass123",
            "full_name": "Other User",
            "phone": "0771111111",
            "role": "customer",
            "district": "Colombo"
        })
        other_token = res.json()["access_token"]
        
        # Try to get messages
        res = requests.get(f"{BASE_URL}/api/chat/messages/{booking_with_quote['booking_id']}", 
                          headers={"Authorization": f"Bearer {other_token}"})
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("✓ Unauthorized user cannot access chat (403)")
    
    def test_send_chat_unauthorized(self, booking_with_quote):
        """User not part of booking cannot send messages"""
        unique_id = str(uuid.uuid4())[:8]
        res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_unauth_{unique_id}@test.com",
            "password": "testpass123",
            "full_name": "Unauthorized User",
            "phone": "0772222222",
            "role": "customer",
            "district": "Colombo"
        })
        other_token = res.json()["access_token"]
        
        res = requests.post(f"{BASE_URL}/api/chat/send", json={
            "booking_id": booking_with_quote["booking_id"],
            "message": "Trying to send unauthorized"
        }, headers={"Authorization": f"Bearer {other_token}"})
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("✓ Unauthorized user cannot send chat messages (403)")
    
    def test_get_conversations_list(self, booking_with_quote):
        """Get list of conversations for user"""
        res = requests.get(f"{BASE_URL}/api/chat/conversations", 
                          headers={"Authorization": f"Bearer {booking_with_quote['customer_token']}"})
        
        assert res.status_code == 200, f"Get conversations failed: {res.text}"
        data = res.json()
        assert "conversations" in data
        conversations = data["conversations"]
        
        # Find our test booking
        found = False
        for c in conversations:
            if c["booking_id"] == booking_with_quote["booking_id"]:
                found = True
                assert "other_user_name" in c
                assert "last_message" in c
                assert "unread_count" in c
                break
        
        assert found, "Test booking not found in conversations"
        print(f"✓ Got {len(conversations)} conversations")
    
    def test_chat_on_nonexistent_booking(self, customer_credentials):
        """Send chat on nonexistent booking returns 404"""
        res = requests.post(f"{BASE_URL}/api/chat/send", json={
            "booking_id": "nonexistent-id",
            "message": "Test message"
        }, headers={"Authorization": f"Bearer {customer_credentials['token']}"})
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"
        print("✓ Chat on nonexistent booking returns 404")

    # ============================
    # NOTIFICATION TESTS
    # ============================
    
    def test_get_notifications(self, booking_with_quote):
        """Get notifications for user"""
        # Wait a bit for notifications to be created
        time.sleep(0.5)
        
        # Handyman should have notification about new booking
        res = requests.get(f"{BASE_URL}/api/notifications", 
                          headers={"Authorization": f"Bearer {booking_with_quote['handyman_token']}"})
        
        assert res.status_code == 200, f"Get notifications failed: {res.text}"
        data = res.json()
        assert "notifications" in data
        assert "unread_count" in data
        print(f"✓ Handyman has {len(data['notifications'])} notifications, {data['unread_count']} unread")
    
    def test_customer_notifications_from_quote(self, booking_with_quote):
        """Customer should have notification from quote"""
        res = requests.get(f"{BASE_URL}/api/notifications", 
                          headers={"Authorization": f"Bearer {booking_with_quote['customer_token']}"})
        
        assert res.status_code == 200, f"Get notifications failed: {res.text}"
        data = res.json()
        
        # Should have quote notification
        quote_notif = None
        for n in data["notifications"]:
            if "Quote" in n.get("title", "") or "quote" in n.get("message", "").lower():
                quote_notif = n
                break
        
        assert quote_notif is not None, "Quote notification not found"
        print(f"✓ Customer received quote notification: {quote_notif['title']}")
    
    def test_mark_single_notification_read(self, booking_with_quote):
        """Mark single notification as read"""
        # Get notifications first
        res = requests.get(f"{BASE_URL}/api/notifications", 
                          headers={"Authorization": f"Bearer {booking_with_quote['customer_token']}"})
        notifications = res.json()["notifications"]
        
        if notifications:
            notif_id = notifications[0]["id"]
            res = requests.put(f"{BASE_URL}/api/notifications/{notif_id}/read", 
                              headers={"Authorization": f"Bearer {booking_with_quote['customer_token']}"})
            assert res.status_code == 200, f"Mark read failed: {res.text}"
            print(f"✓ Marked notification {notif_id} as read")
        else:
            pytest.skip("No notifications to mark as read")
    
    def test_mark_all_notifications_read(self, booking_with_quote):
        """Mark all notifications as read"""
        res = requests.put(f"{BASE_URL}/api/notifications/read-all", json={},
                          headers={"Authorization": f"Bearer {booking_with_quote['handyman_token']}"})
        
        assert res.status_code == 200, f"Mark all read failed: {res.text}"
        
        # Verify unread is 0
        res = requests.get(f"{BASE_URL}/api/notifications", 
                          headers={"Authorization": f"Bearer {booking_with_quote['handyman_token']}"})
        assert res.json()["unread_count"] == 0, "Unread count should be 0"
        print("✓ Marked all notifications as read")
    
    def test_chat_creates_notification(self, booking_with_quote):
        """Sending chat message creates notification for recipient"""
        # Clear notifications first
        requests.put(f"{BASE_URL}/api/notifications/read-all", json={},
                    headers={"Authorization": f"Bearer {booking_with_quote['handyman_token']}"})
        
        # Customer sends message
        requests.post(f"{BASE_URL}/api/chat/send", json={
            "booking_id": booking_with_quote["booking_id"],
            "message": "Testing notification from chat"
        }, headers={"Authorization": f"Bearer {booking_with_quote['customer_token']}"})
        
        time.sleep(0.3)
        
        # Handyman should have notification
        res = requests.get(f"{BASE_URL}/api/notifications", 
                          headers={"Authorization": f"Bearer {booking_with_quote['handyman_token']}"})
        data = res.json()
        
        # Look for chat notification
        chat_notif = None
        for n in data["notifications"]:
            if "message" in n.get("title", "").lower() or n.get("type") == "chat":
                chat_notif = n
                break
        
        assert chat_notif is not None, "Chat notification not found"
        print(f"✓ Chat message created notification: {chat_notif['title']}")

    # ============================
    # PAYHERE TESTS
    # ============================
    
    def test_payhere_not_configured(self, booking_with_quote):
        """PayHere checkout returns 503 when not configured"""
        res = requests.post(f"{BASE_URL}/api/payments/payhere-checkout", json={
            "booking_id": booking_with_quote["booking_id"],
            "origin_url": "https://test.com",
            "gateway": "payhere"
        }, headers={"Authorization": f"Bearer {booking_with_quote['customer_token']}"})
        
        assert res.status_code == 503, f"Expected 503, got {res.status_code}"
        assert "not configured" in res.json().get("detail", "").lower()
        print("✓ PayHere returns 503 when not configured (expected)")
    
    def test_payhere_booking_not_found(self, customer_credentials):
        """PayHere checkout with nonexistent booking returns 404"""
        res = requests.post(f"{BASE_URL}/api/payments/payhere-checkout", json={
            "booking_id": "nonexistent-id",
            "origin_url": "https://test.com",
            "gateway": "payhere"
        }, headers={"Authorization": f"Bearer {customer_credentials['token']}"})
        
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"
        print("✓ PayHere with nonexistent booking returns 404")

    # ============================
    # BOOKING STATUS NOTIFICATIONS
    # ============================
    
    def test_booking_status_notifications(self, customer_credentials, handyman_credentials):
        """Notifications are created when booking status changes"""
        customer_token = customer_credentials["token"]
        handyman_token = handyman_credentials["token"]
        handyman_id = handyman_credentials["user_id"]
        
        # Clear existing notifications
        requests.put(f"{BASE_URL}/api/notifications/read-all", json={},
                    headers={"Authorization": f"Bearer {customer_token}"})
        
        # Create new booking
        res = requests.post(f"{BASE_URL}/api/bookings/create", json={
            "handyman_id": handyman_id,
            "service_id": "electrician",
            "description": "Test notification booking",
            "preferred_date": "2026-02-20",
            "address": "456 Test Ave",
            "district": "Colombo",
            "phone": "0771234567"
        }, headers={"Authorization": f"Bearer {customer_token}"})
        booking_id = res.json()["booking"]["id"]
        
        time.sleep(0.3)
        
        # Check handyman got notification
        res = requests.get(f"{BASE_URL}/api/notifications", 
                          headers={"Authorization": f"Bearer {handyman_token}"})
        notifs = res.json()["notifications"]
        
        booking_notif = None
        for n in notifs:
            if "booking" in n.get("title", "").lower() or "request" in n.get("title", "").lower():
                booking_notif = n
                break
        
        assert booking_notif is not None, "Booking request notification not found"
        print(f"✓ Handyman received booking notification: {booking_notif['title']}")

    # ============================
    # EXISTING FEATURES STILL WORK
    # ============================
    
    def test_existing_services_endpoint(self):
        """Services endpoint still works"""
        res = requests.get(f"{BASE_URL}/api/services")
        assert res.status_code == 200
        data = res.json()
        assert "services" in data
        assert len(data["services"]) > 0
        print(f"✓ Services endpoint works ({len(data['services'])} services)")
    
    def test_existing_auth_login(self):
        """Auth login still works"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@bassbass.lk",
            "password": "admin123"
        })
        assert res.status_code == 200
        assert "access_token" in res.json()
        print("✓ Auth login works")
    
    def test_existing_admin_stats(self):
        """Admin statistics still works"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@bassbass.lk",
            "password": "admin123"
        })
        admin_token = res.json()["access_token"]
        
        res = requests.get(f"{BASE_URL}/api/admin/statistics", 
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        data = res.json()
        assert "total_customers" in data
        assert "total_bookings" in data
        print(f"✓ Admin stats works (bookings: {data['total_bookings']}, customers: {data['total_customers']})")
