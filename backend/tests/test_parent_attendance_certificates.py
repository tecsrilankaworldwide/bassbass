"""
Test Suite for Parent Portal, Attendance System, and Certificate PDF Generation
Features: 
- Parent Portal: Link child, view progress, attendance, certificates, payments
- Attendance Manager: Create sessions, mark attendance (bulk)
- Certificate Generation: Generate PDF certificates, download by ID
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://topbass-staging.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_CREDENTIALS = {"email": "admin@tecaikids.com", "password": "admin123"}
PARENT_CREDENTIALS = {"email": "parent.test@test.com", "password": "test123"}
STUDENT_CREDENTIALS = {"email": "sri.foundation@test.com", "password": "test123"}
STUDENT_INDEX = "SRI-F-1001"


class TestAuthentication:
    """Test authentication for different user roles"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/login", json=ADMIN_CREDENTIALS)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful: {data['user']['email']}")
    
    def test_parent_login(self):
        """Test parent login"""
        response = requests.post(f"{BASE_URL}/api/login", json=PARENT_CREDENTIALS)
        assert response.status_code == 200, f"Parent login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "parent"
        print(f"✓ Parent login successful: {data['user']['email']}")
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/login", json=STUDENT_CREDENTIALS)
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "student"
        assert data["user"]["student_index"] == STUDENT_INDEX
        print(f"✓ Student login successful: {data['user']['student_index']}")


@pytest.fixture
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/login", json=ADMIN_CREDENTIALS)
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Admin authentication failed")


@pytest.fixture
def parent_token():
    """Get parent authentication token"""
    response = requests.post(f"{BASE_URL}/api/login", json=PARENT_CREDENTIALS)
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Parent authentication failed")


@pytest.fixture
def student_token():
    """Get student authentication token"""
    response = requests.post(f"{BASE_URL}/api/login", json=STUDENT_CREDENTIALS)
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Student authentication failed")


@pytest.fixture
def student_id():
    """Get student ID from login"""
    response = requests.post(f"{BASE_URL}/api/login", json=STUDENT_CREDENTIALS)
    if response.status_code == 200:
        return response.json()["user"]["id"]
    pytest.skip("Could not get student ID")


class TestParentPortal:
    """Test Parent Portal functionality"""
    
    def test_get_parent_children(self, parent_token):
        """Test getting linked children for parent"""
        headers = {"Authorization": f"Bearer {parent_token}"}
        response = requests.get(f"{BASE_URL}/api/parent/children", headers=headers)
        
        assert response.status_code == 200, f"Failed to get children: {response.text}"
        data = response.json()
        assert "children" in data
        print(f"✓ Parent has {len(data['children'])} linked children")
        
        # If children exist, verify structure
        if data["children"]:
            child = data["children"][0]
            assert "student" in child
            assert "gamification" in child
            assert "link_id" in child
            print(f"✓ Child data structure verified: {child['student'].get('full_name')}")
    
    def test_link_child_with_invalid_index(self, parent_token):
        """Test linking child with invalid student index"""
        headers = {"Authorization": f"Bearer {parent_token}"}
        response = requests.post(
            f"{BASE_URL}/api/parent/link-child",
            headers=headers,
            json={"student_index": "INVALID-INDEX-999"}
        )
        
        assert response.status_code == 404, f"Expected 404 for invalid index: {response.text}"
        print("✓ Invalid student index correctly rejected")
    
    def test_link_child_with_valid_index(self, parent_token):
        """Test linking child with valid student index (may already be linked)"""
        headers = {"Authorization": f"Bearer {parent_token}"}
        response = requests.post(
            f"{BASE_URL}/api/parent/link-child",
            headers=headers,
            json={"student_index": STUDENT_INDEX}
        )
        
        # Either success (200) or already linked (400)
        assert response.status_code in [200, 400], f"Unexpected response: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True
            print(f"✓ Successfully linked child: {STUDENT_INDEX}")
        else:
            print(f"✓ Child already linked (expected): {STUDENT_INDEX}")
    
    def test_get_child_progress(self, parent_token, student_id):
        """Test getting child progress data"""
        headers = {"Authorization": f"Bearer {parent_token}"}
        response = requests.get(
            f"{BASE_URL}/api/parent/child/{student_id}/progress",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to get progress: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "gamification" in data
        assert "attendance" in data
        assert "certificates" in data
        assert "recent_quizzes" in data
        
        # Verify attendance structure
        assert "records" in data["attendance"]
        assert "attendance_rate" in data["attendance"]
        
        print(f"✓ Child progress retrieved successfully")
        print(f"  - Attendance rate: {data['attendance']['attendance_rate']}%")
        print(f"  - Certificates: {len(data['certificates'])}")
        print(f"  - Recent quizzes: {len(data['recent_quizzes'])}")
    
    def test_get_child_payments(self, parent_token, student_id):
        """Test getting child payment history"""
        headers = {"Authorization": f"Bearer {parent_token}"}
        response = requests.get(
            f"{BASE_URL}/api/parent/child/{student_id}/payments",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to get payments: {response.text}"
        data = response.json()
        
        assert "payments" in data
        assert "total_paid" in data
        
        print(f"✓ Payment history retrieved: {len(data['payments'])} payments, total: ${data['total_paid']}")
    
    def test_unauthorized_access_to_child_progress(self, student_token, student_id):
        """Test that students cannot access parent endpoints"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(
            f"{BASE_URL}/api/parent/child/{student_id}/progress",
            headers=headers
        )
        
        # Should fail - student doesn't have parent-child link
        assert response.status_code == 403, f"Expected 403 for unauthorized access: {response.text}"
        print("✓ Unauthorized access correctly blocked")


class TestAttendanceSystem:
    """Test Attendance Manager functionality"""
    
    def test_create_class_session(self, admin_token):
        """Test creating a new class session"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        session_data = {
            "title": f"TEST_Session_{uuid.uuid4().hex[:8]}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "16:00",
            "age_group": "4-6",
            "zoom_link": "https://zoom.us/j/test123",
            "duration_minutes": 60
        }
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/class",
            headers=headers,
            json=session_data
        )
        
        assert response.status_code == 200, f"Failed to create session: {response.text}"
        data = response.json()
        
        assert data["success"] == True
        assert "session" in data
        assert data["session"]["title"] == session_data["title"]
        assert data["session"]["age_group"] == "4-6"
        
        print(f"✓ Class session created: {data['session']['id']}")
        return data["session"]["id"]
    
    def test_get_class_sessions(self, admin_token):
        """Test getting class sessions list"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/attendance/classes",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to get sessions: {response.text}"
        data = response.json()
        
        assert "sessions" in data
        print(f"✓ Retrieved {len(data['sessions'])} class sessions")
        
        if data["sessions"]:
            session = data["sessions"][0]
            assert "id" in session
            assert "title" in session
            assert "date" in session
            print(f"  - Latest session: {session['title']} on {session['date']}")
            return session["id"]
        return None
    
    def test_get_session_attendance(self, admin_token):
        """Test getting attendance for a session"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First get sessions
        sessions_response = requests.get(
            f"{BASE_URL}/api/attendance/classes",
            headers=headers
        )
        
        if sessions_response.status_code != 200 or not sessions_response.json().get("sessions"):
            # Create a session first
            session_data = {
                "title": f"TEST_Attendance_Session_{uuid.uuid4().hex[:8]}",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "15:00",
                "age_group": "4-6",
                "duration_minutes": 45
            }
            create_response = requests.post(
                f"{BASE_URL}/api/attendance/class",
                headers=headers,
                json=session_data
            )
            session_id = create_response.json()["session"]["id"]
        else:
            session_id = sessions_response.json()["sessions"][0]["id"]
        
        # Get session attendance
        response = requests.get(
            f"{BASE_URL}/api/attendance/session/{session_id}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to get session attendance: {response.text}"
        data = response.json()
        
        assert "session" in data
        assert "attendance" in data
        assert "all_students" in data
        assert "summary" in data
        
        print(f"✓ Session attendance retrieved")
        print(f"  - Total students: {data['summary']['total_students']}")
        print(f"  - Present: {data['summary']['present']}")
        print(f"  - Absent: {data['summary']['absent']}")
        
        return session_id, data["all_students"]
    
    def test_mark_bulk_attendance(self, admin_token, student_id):
        """Test marking bulk attendance"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a new session for testing
        session_data = {
            "title": f"TEST_Bulk_Attendance_{uuid.uuid4().hex[:8]}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "14:00",
            "age_group": "4-6",
            "duration_minutes": 60
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/attendance/class",
            headers=headers,
            json=session_data
        )
        
        assert create_response.status_code == 200
        session_id = create_response.json()["session"]["id"]
        
        # Mark bulk attendance
        bulk_data = {
            "session_id": session_id,
            "attendance": [
                {"student_id": student_id, "status": "present"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/mark-bulk",
            headers=headers,
            json=bulk_data
        )
        
        assert response.status_code == 200, f"Failed to mark bulk attendance: {response.text}"
        data = response.json()
        
        assert data["success"] == True
        assert data["marked_count"] >= 1
        
        print(f"✓ Bulk attendance marked: {data['marked_count']} students")
    
    def test_mark_single_attendance(self, admin_token, student_id):
        """Test marking attendance for a single student"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a session
        session_data = {
            "title": f"TEST_Single_Attendance_{uuid.uuid4().hex[:8]}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "13:00",
            "age_group": "4-6",
            "duration_minutes": 45
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/attendance/class",
            headers=headers,
            json=session_data
        )
        
        session_id = create_response.json()["session"]["id"]
        
        # Mark single attendance
        attendance_data = {
            "session_id": session_id,
            "student_id": student_id,
            "status": "late",
            "notes": "Arrived 10 minutes late"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/mark",
            headers=headers,
            json=attendance_data
        )
        
        assert response.status_code == 200, f"Failed to mark attendance: {response.text}"
        data = response.json()
        
        assert data["success"] == True
        assert data["record"]["status"] == "late"
        
        print(f"✓ Single attendance marked: {data['record']['status']}")
    
    def test_get_student_attendance_report(self, admin_token, student_id):
        """Test getting student attendance report"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/attendance/student/{student_id}/report",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to get report: {response.text}"
        data = response.json()
        
        assert "attendance" in data
        assert "summary" in data
        assert "total_classes" in data["summary"]
        assert "attendance_rate" in data["summary"]
        
        print(f"✓ Student attendance report retrieved")
        print(f"  - Total classes: {data['summary']['total_classes']}")
        print(f"  - Attendance rate: {data['summary']['attendance_rate']}%")


class TestCertificateGeneration:
    """Test Certificate PDF Generation functionality"""
    
    def test_generate_certificate(self, admin_token, student_id):
        """Test generating a certificate for a student"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        cert_data = {
            "student_id": student_id,
            "type": "completion",
            "course_name": "TEST_Future-Ready Learning Program"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/certificates/generate",
            headers=headers,
            json=cert_data
        )
        
        assert response.status_code == 200, f"Failed to generate certificate: {response.text}"
        data = response.json()
        
        assert data["success"] == True
        assert "certificate" in data
        
        cert = data["certificate"]
        assert "id" in cert
        assert "certificate_number" in cert
        assert cert["student_id"] == student_id
        assert cert["certificate_type"] == "completion"
        assert cert["course_name"] == "TEST_Future-Ready Learning Program"
        
        print(f"✓ Certificate generated: {cert['certificate_number']}")
        return cert["id"], cert["certificate_number"]
    
    def test_download_certificate_pdf(self, admin_token, student_id):
        """Test downloading certificate as PDF"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First generate a certificate
        cert_data = {
            "student_id": student_id,
            "type": "achievement",
            "course_name": "TEST_AI Fundamentals"
        }
        
        gen_response = requests.post(
            f"{BASE_URL}/api/certificates/generate",
            headers=headers,
            json=cert_data
        )
        
        assert gen_response.status_code == 200
        cert_id = gen_response.json()["certificate"]["id"]
        
        # Download PDF (no auth required for PDF download)
        pdf_response = requests.get(f"{BASE_URL}/api/certificates/{cert_id}/pdf")
        
        assert pdf_response.status_code == 200, f"Failed to download PDF: {pdf_response.text}"
        assert pdf_response.headers.get("content-type") == "application/pdf"
        
        # Verify PDF content starts with PDF header
        assert pdf_response.content[:4] == b'%PDF', "Response is not a valid PDF"
        
        print(f"✓ Certificate PDF downloaded successfully ({len(pdf_response.content)} bytes)")
    
    def test_get_student_certificates(self, admin_token, student_id):
        """Test getting all certificates for a student"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/certificates/student/{student_id}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to get certificates: {response.text}"
        data = response.json()
        
        assert "certificates" in data
        print(f"✓ Retrieved {len(data['certificates'])} certificates for student")
        
        if data["certificates"]:
            cert = data["certificates"][0]
            assert "certificate_number" in cert
            assert "course_name" in cert
            print(f"  - Latest: {cert['certificate_number']} - {cert['course_name']}")
    
    def test_verify_certificate_public(self, admin_token, student_id):
        """Test public certificate verification"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a certificate first
        cert_data = {
            "student_id": student_id,
            "type": "participation",
            "course_name": "TEST_Logical Thinking Workshop"
        }
        
        gen_response = requests.post(
            f"{BASE_URL}/api/certificates/generate",
            headers=headers,
            json=cert_data
        )
        
        cert_number = gen_response.json()["certificate"]["certificate_number"]
        
        # Verify certificate (public endpoint - no auth)
        verify_response = requests.get(f"{BASE_URL}/api/certificates/verify/{cert_number}")
        
        assert verify_response.status_code == 200, f"Failed to verify: {verify_response.text}"
        data = verify_response.json()
        
        assert data["verified"] == True
        assert data["certificate"]["certificate_number"] == cert_number
        assert data["organization"] == "TEC Future-Ready Learning"
        
        print(f"✓ Certificate verified: {cert_number}")
    
    def test_verify_invalid_certificate(self):
        """Test verification of invalid certificate number"""
        response = requests.get(f"{BASE_URL}/api/certificates/verify/INVALID-CERT-12345")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["verified"] == False
        print("✓ Invalid certificate correctly rejected")
    
    def test_download_nonexistent_certificate(self):
        """Test downloading non-existent certificate"""
        response = requests.get(f"{BASE_URL}/api/certificates/nonexistent-id-12345/pdf")
        
        assert response.status_code == 404
        print("✓ Non-existent certificate correctly returns 404")


class TestIntegration:
    """Integration tests for Parent Portal viewing certificates and attendance"""
    
    def test_parent_can_view_child_certificates(self, parent_token, student_id):
        """Test that parent can view child's certificates through progress endpoint"""
        headers = {"Authorization": f"Bearer {parent_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/parent/child/{student_id}/progress",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "certificates" in data
        print(f"✓ Parent can view {len(data['certificates'])} certificates for child")
    
    def test_parent_can_view_child_attendance(self, parent_token, student_id):
        """Test that parent can view child's attendance through progress endpoint"""
        headers = {"Authorization": f"Bearer {parent_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/parent/child/{student_id}/progress",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "attendance" in data
        assert "records" in data["attendance"]
        assert "attendance_rate" in data["attendance"]
        
        print(f"✓ Parent can view attendance: {data['attendance']['attendance_rate']}% rate")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
