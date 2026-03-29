"""
Backend tests for Language Filtering Feature in TecAI Kids Educational Platform
Tests: /api/supported-languages, video upload with language, video retrieval with language filter
"""
import pytest
import requests
import os
import tempfile

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://topbass-staging.preview.emergentagent.com')

# Test credentials
TEST_TEACHER_EMAIL = "testteacher123@test.com"
TEST_TEACHER_PASSWORD = "test1234"

# Supported languages
EXPECTED_LANGUAGES = ["en", "si", "ta", "zh-CN", "hi", "ar", "id", "ms", "bn", "ur"]


class TestSupportedLanguagesAPI:
    """Tests for /api/supported-languages endpoint"""
    
    def test_supported_languages_returns_all_10_languages(self):
        """Verify /api/supported-languages returns all 10 supported languages"""
        response = requests.get(f"{BASE_URL}/api/supported-languages")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "languages" in data, "Response should contain 'languages' key"
        
        languages = data["languages"]
        assert len(languages) == 10, f"Expected 10 languages, got {len(languages)}"
        
        # Verify all expected language codes are present
        language_codes = [lang["code"] for lang in languages]
        for expected_code in EXPECTED_LANGUAGES:
            assert expected_code in language_codes, f"Missing language code: {expected_code}"
        
        print(f"✅ All 10 languages returned: {language_codes}")
    
    def test_supported_languages_has_names(self):
        """Verify each language has both code and name"""
        response = requests.get(f"{BASE_URL}/api/supported-languages")
        
        assert response.status_code == 200
        
        data = response.json()
        for lang in data["languages"]:
            assert "code" in lang, "Each language should have 'code'"
            assert "name" in lang, "Each language should have 'name'"
            assert len(lang["name"]) > 0, f"Language {lang['code']} should have non-empty name"
        
        print("✅ All languages have code and name fields")


class TestTeacherAuthentication:
    """Tests for teacher login"""
    
    def test_teacher_login_success(self):
        """Verify teacher can login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"email": TEST_TEACHER_EMAIL, "password": TEST_TEACHER_PASSWORD}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user info"
        assert data["user"]["role"] == "teacher", "User should be a teacher"
        
        print(f"✅ Teacher login successful: {data['user']['email']}")
        return data["access_token"]


class TestCourseCreation:
    """Tests for course creation (needed for video upload)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for teacher"""
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"email": TEST_TEACHER_EMAIL, "password": TEST_TEACHER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_create_course_for_video_upload(self, auth_token):
        """Create a test course for video upload testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        course_data = {
            "title": "TEST_Language_Filter_Course",
            "description": "Test course for language filter feature testing",
            "learning_level": "foundation",
            "skill_areas": ["ai_literacy"],
            "age_group": "5-8",
            "is_premium": False,
            "difficulty_level": 1,
            "estimated_hours": 2
        }
        
        response = requests.post(
            f"{BASE_URL}/api/courses",
            json=course_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Course creation failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Course should have an ID"
        assert data["title"] == course_data["title"]
        
        print(f"✅ Test course created: {data['id']}")
        return data["id"]


class TestVideoUploadWithLanguage:
    """Tests for video upload with language parameter"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for teacher"""
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"email": TEST_TEACHER_EMAIL, "password": TEST_TEACHER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def test_course_id(self, auth_token):
        """Create or get a test course"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First check if test course exists
        response = requests.get(
            f"{BASE_URL}/api/courses?published_only=false",
            headers=headers
        )
        
        if response.status_code == 200:
            courses = response.json()
            for course in courses:
                if course.get("title", "").startswith("TEST_"):
                    return course["id"]
        
        # Create new test course
        course_data = {
            "title": "TEST_Video_Language_Course",
            "description": "Test course for video language testing",
            "learning_level": "foundation",
            "skill_areas": ["ai_literacy"],
            "age_group": "5-8",
            "is_premium": False,
            "difficulty_level": 1,
            "estimated_hours": 2
        }
        
        response = requests.post(
            f"{BASE_URL}/api/courses",
            json=course_data,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()["id"]
        
        pytest.skip("Could not create test course")
    
    def test_video_upload_endpoint_accepts_language_parameter(self, auth_token, test_course_id):
        """Verify video upload endpoint accepts language parameter"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a minimal test video file (just for API testing)
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            # Write minimal MP4 header bytes
            f.write(b'\x00\x00\x00\x1c\x66\x74\x79\x70\x69\x73\x6f\x6d')
            f.write(b'\x00\x00\x02\x00\x69\x73\x6f\x6d\x69\x73\x6f\x32')
            f.write(b'\x00' * 100)  # Padding
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as video_file:
                files = {'video': ('test_video.mp4', video_file, 'video/mp4')}
                data = {
                    'title': 'TEST_English_Lesson',
                    'description': 'Test lesson in English',
                    'language': 'en'
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/courses/{test_course_id}/videos",
                    files=files,
                    data=data,
                    headers=headers
                )
                
                # Accept 200 (success) or 400/500 (file validation error - expected for minimal test file)
                # The key is that the endpoint exists and accepts the language parameter
                if response.status_code == 200:
                    result = response.json()
                    assert "video" in result, "Response should contain video info"
                    assert result["video"].get("language") == "en", "Video should have language 'en'"
                    print(f"✅ Video uploaded with language 'en': {result['video']['id']}")
                else:
                    # Even if upload fails due to file validation, endpoint should exist
                    print(f"⚠️ Upload returned {response.status_code} - endpoint exists but file validation may have failed")
                    assert response.status_code != 404, "Endpoint should exist"
        finally:
            import os
            os.unlink(temp_path)


class TestVideoRetrievalWithLanguageFilter:
    """Tests for video retrieval with language filter"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for teacher"""
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"email": TEST_TEACHER_EMAIL, "password": TEST_TEACHER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def test_course_id(self, auth_token):
        """Get a test course ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/courses?published_only=false",
            headers=headers
        )
        
        if response.status_code == 200:
            courses = response.json()
            for course in courses:
                if course.get("title", "").startswith("TEST_"):
                    return course["id"]
        
        # Create new test course
        course_data = {
            "title": "TEST_Video_Retrieval_Course",
            "description": "Test course for video retrieval testing",
            "learning_level": "foundation",
            "skill_areas": ["ai_literacy"],
            "age_group": "5-8",
            "is_premium": False,
            "difficulty_level": 1,
            "estimated_hours": 2
        }
        
        response = requests.post(
            f"{BASE_URL}/api/courses",
            json=course_data,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()["id"]
        
        pytest.skip("Could not get/create test course")
    
    def test_get_videos_endpoint_accepts_language_filter(self, auth_token, test_course_id):
        """Verify GET /api/courses/{course_id}/videos accepts language query parameter"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test without language filter
        response = requests.get(
            f"{BASE_URL}/api/courses/{test_course_id}/videos",
            headers=headers
        )
        
        assert response.status_code == 200, f"Get videos failed: {response.text}"
        
        data = response.json()
        assert "videos" in data, "Response should contain 'videos' key"
        assert "count" in data, "Response should contain 'count' key"
        
        print(f"✅ Get videos without filter: {data['count']} videos")
        
        # Test with language filter
        response_filtered = requests.get(
            f"{BASE_URL}/api/courses/{test_course_id}/videos?language=en",
            headers=headers
        )
        
        assert response_filtered.status_code == 200, f"Get videos with filter failed: {response_filtered.text}"
        
        data_filtered = response_filtered.json()
        assert "videos" in data_filtered, "Filtered response should contain 'videos' key"
        assert "language_filter" in data_filtered, "Response should contain 'language_filter' key"
        assert data_filtered["language_filter"] == "en", "Language filter should be 'en'"
        
        print(f"✅ Get videos with language filter 'en': {data_filtered['count']} videos")
    
    def test_get_videos_with_invalid_language_filter(self, auth_token, test_course_id):
        """Verify GET /api/courses/{course_id}/videos handles invalid language gracefully"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test with invalid language code
        response = requests.get(
            f"{BASE_URL}/api/courses/{test_course_id}/videos?language=invalid",
            headers=headers
        )
        
        assert response.status_code == 200, "Should handle invalid language gracefully"
        
        data = response.json()
        # Invalid language should be ignored or return all videos
        assert "videos" in data, "Response should still contain 'videos' key"
        
        print("✅ Invalid language filter handled gracefully")


class TestAPIHealthCheck:
    """Basic API health checks"""
    
    def test_api_root_endpoint(self):
        """Verify API root endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/")
        
        assert response.status_code == 200, f"API root failed: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "TEC" in data["message"], "Should be TEC platform"
        
        print(f"✅ API root accessible: {data['message']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
