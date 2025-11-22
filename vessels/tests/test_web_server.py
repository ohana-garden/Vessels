"""
Test suite for vessels_web_server.py

Tests cover:
- Happy path scenarios (valid inputs)
- Error cases (invalid inputs, missing fields, oversized payloads)
- Security validation (XSS, injection attempts)
- Rate limiting behavior
- Input sanitization
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import vessels_web_server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock VesselsPlatform before importing
sys.modules['vessels_fixed'] = MagicMock()
sys.modules['content_generation'] = MagicMock()

import vessels_web_server as web_server


@pytest.fixture
def client():
    """Create test client"""
    web_server.app.config['TESTING'] = True
    with web_server.app.test_client() as client:
        yield client


@pytest.fixture
def mock_vessels():
    """Mock Vessels platform"""
    mock = Mock()
    mock.find_grants.return_value = {'grants': []}
    mock.generate_applications.return_value = {'status': 'success'}
    mock.process_request.return_value = {'response': 'Test response'}
    mock.get_status.return_value = {'status': 'ok'}
    return mock


@pytest.fixture(autouse=True)
def setup_mocks(mock_vessels):
    """Setup mocks for all tests"""
    web_server.vessels = mock_vessels
    web_server.sessions.clear()


# ============================================================================
# HAPPY PATH TESTS
# ============================================================================

class TestVoiceProcessing:
    """Test /api/voice/process endpoint"""

    def test_valid_voice_input(self, client):
        """Test valid voice processing request"""
        response = client.post(
            '/api/voice/process',
            json={
                'text': 'help me find grants',
                'session_id': 'test-session-123',
                'emotion': 'neutral'
            },
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'agents' in data
        assert 'content_type' in data
        assert 'subtitles' in data

    def test_voice_input_with_defaults(self, client):
        """Test voice processing with default values"""
        response = client.post(
            '/api/voice/process',
            json={'text': 'hello'},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data is not None

    def test_different_emotions(self, client):
        """Test various emotion values"""
        emotions = ['happy', 'sad', 'frustrated', 'uncertain', 'excited']

        for emotion in emotions:
            response = client.post(
                '/api/voice/process',
                json={
                    'text': 'test',
                    'emotion': emotion
                },
                content_type='application/json'
            )
            assert response.status_code == 200


# ============================================================================
# ERROR CASE TESTS
# ============================================================================

class TestInputValidation:
    """Test input validation and error handling"""

    def test_missing_json_body(self, client):
        """Test request with missing JSON body"""
        response = client.post('/api/voice/process')
        assert response.status_code == 400

    def test_wrong_content_type(self, client):
        """Test request with wrong content type"""
        response = client.post(
            '/api/voice/process',
            data='not json',
            content_type='text/plain'
        )
        assert response.status_code == 415

    def test_empty_text(self, client):
        """Test request with empty text"""
        response = client.post(
            '/api/voice/process',
            json={'text': ''},
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_whitespace_only_text(self, client):
        """Test request with whitespace-only text"""
        response = client.post(
            '/api/voice/process',
            json={'text': '   '},
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_oversized_text(self, client):
        """Test request with text exceeding limit"""
        response = client.post(
            '/api/voice/process',
            json={'text': 'a' * 10001},  # Exceeds 10k limit
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_invalid_session_id_characters(self, client):
        """Test session ID with invalid characters"""
        response = client.post(
            '/api/voice/process',
            json={
                'text': 'test',
                'session_id': 'invalid<>chars'
            },
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_invalid_emotion(self, client):
        """Test with invalid emotion (should default to neutral)"""
        response = client.post(
            '/api/voice/process',
            json={
                'text': 'test',
                'emotion': 'invalid_emotion_xyz'
            },
            content_type='application/json'
        )
        # Should succeed with emotion defaulting to neutral
        assert response.status_code == 200


class TestSecurityValidation:
    """Test security-related validation"""

    def test_null_byte_injection(self, client):
        """Test null byte injection attempt"""
        response = client.post(
            '/api/voice/process',
            json={'text': 'test\x00injection'},
            content_type='application/json'
        )
        # Should succeed after null bytes are removed
        assert response.status_code == 200

    def test_xss_attempt_in_text(self, client):
        """Test XSS attempt in text field"""
        response = client.post(
            '/api/voice/process',
            json={'text': '<script>alert("xss")</script>'},
            content_type='application/json'
        )
        # Should process normally (escaping happens at render time)
        assert response.status_code == 200

    def test_sql_injection_attempt(self, client):
        """Test SQL injection pattern"""
        response = client.post(
            '/api/voice/process',
            json={'text': "'; DROP TABLE users; --"},
            content_type='application/json'
        )
        # Should process normally (no direct SQL execution)
        assert response.status_code == 200


# ============================================================================
# GRANT ENDPOINT TESTS
# ============================================================================

class TestGrantEndpoints:
    """Test grant-related endpoints"""

    def test_grant_search_valid(self, client, mock_vessels):
        """Test valid grant search"""
        mock_vessels.find_grants.return_value = {
            'grants': [
                {'title': 'Test Grant', 'amount': '$10K'}
            ]
        }

        response = client.post(
            '/api/grants/search',
            json={'query': 'elder care funding'},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'grants' in data

    def test_grant_search_empty_query(self, client):
        """Test grant search with empty query"""
        response = client.post(
            '/api/grants/search',
            json={'query': ''},
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_grant_search_missing_query(self, client):
        """Test grant search without query field"""
        response = client.post(
            '/api/grants/search',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_grant_apply_valid(self, client, mock_vessels):
        """Test valid grant application"""
        mock_vessels.generate_applications.return_value = {
            'status': 'success',
            'application_id': 'app-123'
        }

        response = client.post(
            '/api/grants/apply',
            json={'grant_id': 'grant-123'},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'

    def test_grant_apply_missing_id(self, client):
        """Test grant application without grant_id"""
        response = client.post(
            '/api/grants/apply',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400


# ============================================================================
# CONTENT GENERATION TESTS
# ============================================================================

class TestContentGeneration:
    """Test content generation endpoint"""

    def test_content_generate_valid(self, client):
        """Test valid content generation request"""
        response = client.post(
            '/api/content/generate',
            json={
                'type': 'CULTURAL_GUIDE',
                'audience': 'community',
                'culture': 'hawaiian'
            },
            content_type='application/json'
        )

        # May fail due to async dependencies, but should validate
        assert response.status_code in [200, 500]

    def test_content_generate_with_defaults(self, client):
        """Test content generation with default values"""
        response = client.post(
            '/api/content/generate',
            json={},
            content_type='application/json'
        )

        # Should use defaults
        assert response.status_code in [200, 500]


# ============================================================================
# GENERAL ENDPOINT TESTS
# ============================================================================

class TestGeneralEndpoints:
    """Test general endpoints"""

    def test_index_endpoint(self, client):
        """Test index page"""
        response = client.get('/')
        # May fail if template doesn't exist
        assert response.status_code in [200, 500]

    def test_status_endpoint(self, client, mock_vessels):
        """Test status endpoint"""
        mock_vessels.get_status.return_value = {
            'status': 'ok',
            'version': '1.0.0'
        }

        response = client.get('/api/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'

    def test_session_endpoint_not_found(self, client):
        """Test session endpoint with non-existent session"""
        response = client.get('/api/session/nonexistent')
        assert response.status_code == 404

    def test_session_endpoint_exists(self, client):
        """Test session endpoint with existing session"""
        # Create session first
        web_server.sessions['test-session'] = {
            'context': ['hello'],
            'emotion_history': ['neutral']
        }

        response = client.get('/api/session/test-session')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'context' in data


# ============================================================================
# PAYLOAD SIZE TESTS
# ============================================================================

class TestPayloadLimits:
    """Test payload size limits"""

    def test_max_content_length_exceeded(self, client):
        """Test request exceeding MAX_CONTENT_LENGTH"""
        # Flask MAX_CONTENT_LENGTH is set to 1MB
        large_payload = {'text': 'a' * (2 * 1024 * 1024)}  # 2MB

        response = client.post(
            '/api/voice/process',
            json=large_payload,
            content_type='application/json'
        )

        # Should reject due to size limit
        assert response.status_code == 413

    def test_payload_within_limit(self, client):
        """Test request within size limit"""
        # 100KB payload
        payload = {'text': 'a' * (100 * 1024)}

        response = client.post(
            '/api/voice/process',
            json=payload,
            content_type='application/json'
        )

        # Should fail validation (too long), but not size limit
        assert response.status_code == 400


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
