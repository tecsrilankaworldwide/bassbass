"""
Grade 5 Scholarship Exam Platform - Comprehensive Backend Tests
Tests all roles (admin, student, teacher, parent, marker), 
batch management, and API endpoints.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CREDENTIALS = {
    'admin': {'email': 'admin@exam.lk', 'password': 'admin123'},
    'student': {'email': 'student@test.lk', 'password': 'pass123'},
    'teacher': {'email': 'teacher@test.lk', 'password': 'pass123'},
    'parent': {'email': 'parent@test.lk', 'password': 'pass123'},
    'marker': {'email': 'marker@exam.lk', 'password': 'marker123'},
}

class TestAPIHealth:
    """Health check and basic API connectivity tests"""
    
    def test_api_root_health(self):
        """API root endpoint should return operational status"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'operational'
        assert 'version' in data
        assert 'features' in data
        print(f"✅ API Health OK - Version: {data['version']}")


class TestAuthentication:
    """Login tests for all 5 roles"""
    
    def test_admin_login(self):
        """Admin can login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['admin'])
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['user']['role'] == 'admin'
        assert data['user']['email'] == 'admin@exam.lk'
        print(f"✅ Admin login OK - User: {data['user']['full_name']}")
    
    def test_student_login(self):
        """Student can login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['student'])
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['user']['role'] == 'student'
        assert 'student_id' in data['user']
        print(f"✅ Student login OK - Student ID: {data['user']['student_id']}")
    
    def test_teacher_login(self):
        """Teacher can login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['teacher'])
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['user']['role'] == 'teacher'
        print(f"✅ Teacher login OK - User: {data['user']['full_name']}")
    
    def test_parent_login(self):
        """Parent can login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['parent'])
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['user']['role'] == 'parent'
        assert 'linked_student_id' in data['user']
        print(f"✅ Parent login OK - Linked Student: {data['user']['linked_student_id']}")
    
    def test_marker_login(self):
        """Marker can login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['marker'])
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['user']['role'] == 'marker'
        print(f"✅ Marker login OK - User: {data['user']['full_name']}")
    
    def test_invalid_credentials_rejected(self):
        """Invalid credentials should be rejected"""
        response = requests.post(f"{BASE_URL}/api/login", json={
            'email': 'fake@test.com',
            'password': 'wrongpassword'
        })
        assert response.status_code in [401, 404]
        print("✅ Invalid credentials rejected correctly")


class TestAdminStatistics:
    """Admin statistics API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['admin'])
        return response.json()['access_token']
    
    def test_get_admin_statistics(self, admin_token):
        """Admin can retrieve platform statistics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/statistics",
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected statistics fields
        assert 'total_students' in data
        assert 'total_parents' in data
        assert 'total_markers' in data
        assert 'total_exams' in data
        assert 'total_batches' in data
        assert 'total_teaching_sessions' in data
        assert 'total_attempts' in data
        assert 'pending_marking' in data
        assert 'completed_exams' in data
        
        print(f"✅ Admin statistics OK - Students: {data['total_students']}, Batches: {data['total_batches']}")
    
    def test_statistics_requires_auth(self):
        """Statistics endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/statistics")
        assert response.status_code == 403
        print("✅ Statistics endpoint correctly requires auth")


class TestBatchManagement:
    """Batch/Class management API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['admin'])
        return response.json()['access_token']
    
    def test_list_batches(self, admin_token):
        """Can list all batches"""
        response = requests.get(
            f"{BASE_URL}/api/batches",
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'batches' in data
        assert isinstance(data['batches'], list)
        print(f"✅ List batches OK - Found {len(data['batches'])} batches")
    
    def test_create_batch(self, admin_token):
        """Admin can create a new batch"""
        import uuid
        batch_name = f"TEST_Batch_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/batches/create",
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'name': batch_name,
                'grade': 'grade_5',
                'description': 'Test batch for automated testing',
                'language': 'en'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == batch_name
        assert data['grade'] == 'grade_5'
        assert 'id' in data
        print(f"✅ Create batch OK - ID: {data['id']}")
    
    def test_batches_require_auth(self):
        """Batches endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/batches")
        assert response.status_code == 403
        print("✅ Batches endpoint correctly requires auth")


class TestUserManagement:
    """Admin user management tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['admin'])
        return response.json()['access_token']
    
    def test_list_users(self, admin_token):
        """Admin can list all users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'users' in data
        assert isinstance(data['users'], list)
        assert len(data['users']) > 0
        print(f"✅ List users OK - Found {len(data['users'])} users")


class TestStudentFeatures:
    """Student-specific API tests"""
    
    @pytest.fixture
    def student_token(self):
        """Get student authentication token"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['student'])
        return response.json()['access_token']
    
    def test_student_can_list_exams(self, student_token):
        """Student can view available exams"""
        response = requests.get(
            f"{BASE_URL}/api/exams",
            headers={'Authorization': f'Bearer {student_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'exams' in data or isinstance(data, list)
        print("✅ Student can list exams OK")


class TestTeacherFeatures:
    """Teacher-specific API tests"""
    
    @pytest.fixture
    def teacher_token(self):
        """Get teacher authentication token"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['teacher'])
        return response.json()['access_token']
    
    def test_teacher_can_access_dashboard(self, teacher_token):
        """Teacher can access their dashboard data"""
        # Teacher should be able to list exams
        response = requests.get(
            f"{BASE_URL}/api/exams",
            headers={'Authorization': f'Bearer {teacher_token}'}
        )
        assert response.status_code == 200
        print("✅ Teacher can access dashboard OK")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
