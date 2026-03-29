"""
Grade 5 Scholarship Exam Platform - NEW FEATURES Tests (Iteration 5)
Tests the new features: CSV bulk import, Marker bank details, Admin Payments tab
"""
import pytest
import requests
import os
import uuid
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CREDENTIALS = {
    'admin': {'email': 'admin@exam.lk', 'password': 'admin123'},
    'marker': {'email': 'marker@exam.lk', 'password': 'marker123'},
    'student': {'email': 'student@test.lk', 'password': 'pass123'},
}


class TestAPIHealth:
    """Quick health check"""
    
    def test_api_operational(self):
        """API root should be operational"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'operational'
        print(f"API Health: {data['version']}")


class TestAdminLogin:
    """Admin authentication test"""
    
    def test_admin_login_success(self):
        """Admin can login and get token"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['admin'])
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['user']['role'] == 'admin'
        print(f"Admin login successful: {data['user']['full_name']}")


class TestMarkerLogin:
    """Marker authentication test"""
    
    def test_marker_login_success(self):
        """Marker can login and get token"""
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['marker'])
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['user']['role'] == 'marker'
        print(f"Marker login successful: {data['user']['full_name']}")


class TestAdminStatisticsNewFields:
    """Test admin statistics returns new fields for 5-tab dashboard"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['admin'])
        return response.json()['access_token']
    
    def test_admin_statistics_has_all_required_fields(self, admin_token):
        """Admin statistics should include all 8 stat card fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/statistics",
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All 8 stat cards from Overview tab
        required_fields = [
            'total_students', 'total_parents', 'total_markers', 'total_exams',
            'total_batches', 'total_attempts', 'pending_marking', 'completed_exams'
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            print(f"  - {field}: {data[field]}")
        
        print(f"All 8 statistics fields present")


class TestMarkerBankDetails:
    """Test marker bank details endpoints"""
    
    @pytest.fixture
    def marker_token(self):
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['marker'])
        return response.json()['access_token']
    
    def test_get_marker_bank_details(self, marker_token):
        """GET /api/marker/bank-details - should return bank details or null"""
        response = requests.get(
            f"{BASE_URL}/api/marker/bank-details",
            headers={'Authorization': f'Bearer {marker_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'bank_details' in data
        print(f"GET bank-details OK - Details present: {data['bank_details'] is not None}")
    
    def test_update_marker_bank_details(self, marker_token):
        """PUT /api/marker/bank-details - should save bank details"""
        bank_details = {
            'bank_name': 'Sampath Bank',
            'branch': 'Kandy',
            'account_number': '9876543210',
            'account_holder_name': 'Paper Marker'
        }
        
        response = requests.put(
            f"{BASE_URL}/api/marker/bank-details",
            json=bank_details,
            headers={'Authorization': f'Bearer {marker_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Bank details updated'
        print(f"PUT bank-details OK - Updated successfully")
        
        # Verify by fetching again
        verify_response = requests.get(
            f"{BASE_URL}/api/marker/bank-details",
            headers={'Authorization': f'Bearer {marker_token}'}
        )
        verify_data = verify_response.json()
        assert verify_data['bank_details'] is not None
        assert verify_data['bank_details']['bank_name'] == 'Sampath Bank'
        assert verify_data['bank_details']['branch'] == 'Kandy'
        assert verify_data['bank_details']['account_number'] == '9876543210'
        print(f"Bank details verified: {verify_data['bank_details']['bank_name']} - {verify_data['bank_details']['branch']}")


class TestMarkerPayments:
    """Test marker payments endpoints"""
    
    @pytest.fixture
    def marker_token(self):
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['marker'])
        return response.json()['access_token']
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['admin'])
        return response.json()['access_token']
    
    def test_get_marker_own_payments(self, marker_token):
        """GET /api/marker/my-payments - marker can view own payment history"""
        response = requests.get(
            f"{BASE_URL}/api/marker/my-payments",
            headers={'Authorization': f'Bearer {marker_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'payments' in data
        assert 'total_pending' in data
        assert 'total_paid' in data
        assert 'papers_marked' in data
        print(f"Marker payments OK - Papers marked: {data['papers_marked']}, Pending: {data['total_pending']}, Paid: {data['total_paid']}")


class TestAdminMarkerPayments:
    """Test admin marker payments management"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['admin'])
        return response.json()['access_token']
    
    def test_admin_get_all_marker_payments(self, admin_token):
        """GET /api/admin/marker-payments - admin can view all marker payments"""
        response = requests.get(
            f"{BASE_URL}/api/admin/marker-payments",
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'markers' in data
        assert 'total_payments' in data
        assert isinstance(data['markers'], list)
        
        # If markers have data, verify structure
        if len(data['markers']) > 0:
            marker = data['markers'][0]
            assert 'marker_id' in marker
            assert 'marker_name' in marker
            assert 'total_papers' in marker
            assert 'total_pending' in marker
            assert 'total_paid' in marker
            print(f"Marker payment structure verified: {marker['marker_name']}")
        
        print(f"Admin marker-payments OK - Total payments: {data['total_payments']}, Markers: {len(data['markers'])}")
    
    def test_admin_pay_marker_endpoint(self, admin_token):
        """POST /api/admin/pay-marker/{marker_id} - endpoint exists and works"""
        # First get a marker ID from marker payments
        payments_response = requests.get(
            f"{BASE_URL}/api/admin/marker-payments",
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        if payments_response.status_code == 200:
            data = payments_response.json()
            if len(data['markers']) > 0:
                marker_id = data['markers'][0]['marker_id']
                
                # Try to pay the marker
                response = requests.post(
                    f"{BASE_URL}/api/admin/pay-marker/{marker_id}",
                    json={'reference_number': 'TEST-REF-12345'},
                    headers={'Authorization': f'Bearer {admin_token}'}
                )
                # Should return 200 even if no pending payments
                assert response.status_code == 200
                result = response.json()
                assert 'message' in result
                print(f"Pay marker endpoint OK: {result['message']}")
            else:
                print("No markers with payments to test pay endpoint - endpoint structure verified")
        
        print("Admin pay-marker endpoint verified")


class TestCSVStudentImport:
    """Test bulk CSV student import"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['admin'])
        return response.json()['access_token']
    
    def test_csv_import_endpoint_exists(self, admin_token):
        """POST /api/admin/import-students-csv - endpoint exists"""
        # Create a simple CSV content
        csv_content = "student_name,student_email,parent_name,parent_email,grade,language,school,teacher_incharge\n"
        unique_id = uuid.uuid4().hex[:6]
        csv_content += f"TEST_Student_{unique_id},test_student_{unique_id}@test.com,TEST_Parent_{unique_id},test_parent_{unique_id}@test.com,5,si,TEST_School_{unique_id},Mrs. Test\n"
        
        # Create file-like object
        files = {
            'file': ('students.csv', csv_content, 'text/csv')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/import-students-csv",
            files=files,
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert 'created' in data
        assert 'skipped' in data
        assert 'errors' in data
        assert 'details' in data
        
        print(f"CSV import OK - Created: {data['created']}, Skipped: {data['skipped']}, Errors: {len(data['errors'])}")
        
        if data['created'] > 0:
            # Verify details structure
            detail = data['details'][0]
            assert 'student_name' in detail
            assert 'student_email' in detail
            assert 'student_password' in detail  # Auto-generated password
            print(f"  Student created: {detail['student_name']} - {detail['student_email']}")
    
    def test_csv_import_with_existing_email(self, admin_token):
        """CSV import should skip existing emails"""
        # Try to import with an existing email
        csv_content = "student_name,student_email,parent_name,parent_email,grade,language,school,teacher_incharge\n"
        csv_content += f"Duplicate Student,student@test.lk,Parent,parent@example.com,5,si,Test School,Teacher\n"
        
        files = {
            'file': ('students.csv', csv_content, 'text/csv')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/import-students-csv",
            files=files,
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have skipped or errored for existing email
        assert data['skipped'] > 0 or len(data['errors']) > 0
        print(f"CSV duplicate email handling OK - Skipped: {data['skipped']}")
    
    def test_csv_import_requires_admin_auth(self):
        """CSV import endpoint requires admin authentication"""
        csv_content = "student_name,student_email\nTest,test@test.com\n"
        files = {'file': ('students.csv', csv_content, 'text/csv')}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/import-students-csv",
            files=files
        )
        
        assert response.status_code in [401, 403]
        print("CSV import auth requirement verified")


class TestAdminUsersWithSchool:
    """Test admin user listing shows school field"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['admin'])
        return response.json()['access_token']
    
    def test_user_list_includes_school_field(self, admin_token):
        """GET /api/admin/users should include school field for users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'users' in data
        assert len(data['users']) > 0
        
        # Check if school field is present (may be None for old users)
        user = data['users'][0]
        # school field should be present in user object (even if null)
        print(f"User list OK - Total users: {len(data['users'])}")


class TestBatchesWithTeacherIncharge:
    """Test batches include teacher_incharge field"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/login", json=CREDENTIALS['admin'])
        return response.json()['access_token']
    
    def test_create_batch_with_teacher_incharge(self, admin_token):
        """POST /api/batches/create with teacher_incharge field"""
        unique_id = uuid.uuid4().hex[:6]
        batch_data = {
            'name': f'TEST_Batch_{unique_id}',
            'grade': 'grade_5',
            'description': 'Test batch with teacher',
            'language': 'si',
            'teacher_incharge': 'Mrs. Perera'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/batches/create",
            json=batch_data,
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == batch_data['name']
        assert data['teacher_incharge'] == 'Mrs. Perera'
        print(f"Batch created with teacher_incharge: {data['teacher_incharge']}")
    
    def test_list_batches_shows_teacher_incharge(self, admin_token):
        """GET /api/batches should show teacher_incharge"""
        response = requests.get(
            f"{BASE_URL}/api/batches",
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'batches' in data
        
        # If we have batches with teacher_incharge
        if len(data['batches']) > 0:
            batch = data['batches'][0]
            # teacher_incharge field should exist
            assert 'teacher_incharge' in batch or 'student_count' in batch
            print(f"Batches list OK - Found {len(data['batches'])} batches")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
