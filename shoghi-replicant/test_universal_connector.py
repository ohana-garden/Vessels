#!/usr/bin/env python3
"""
Test suite for universal_connector.py
Tests the universal connector system for external APIs and services
"""

import pytest
import os
from unittest.mock import patch, Mock
from datetime import datetime
from universal_connector import (
    ConnectorType,
    AuthenticationType,
    ConnectorSpecification,
    ConnectorInstance,
    UniversalConnector,
    universal_connector
)


class TestConnectorType:
    """Tests for ConnectorType enum"""

    def test_connector_type_values(self):
        """Test that all connector types have correct values"""
        assert ConnectorType.GOVERNMENT.value == "government"
        assert ConnectorType.FOUNDATION.value == "foundation"
        assert ConnectorType.COMMUNITY.value == "community"
        assert ConnectorType.FINANCIAL.value == "financial"
        assert ConnectorType.DOCUMENT.value == "document"
        assert ConnectorType.API.value == "api"
        assert ConnectorType.DATABASE.value == "database"
        assert ConnectorType.FILE.value == "file"


class TestAuthenticationType:
    """Tests for AuthenticationType enum"""

    def test_authentication_type_values(self):
        """Test that all authentication types have correct values"""
        assert AuthenticationType.NONE.value == "none"
        assert AuthenticationType.API_KEY.value == "api_key"
        assert AuthenticationType.OAUTH.value == "oauth"
        assert AuthenticationType.BASIC.value == "basic"
        assert AuthenticationType.CUSTOM.value == "custom"


class TestUniversalConnector:
    """Tests for UniversalConnector class"""

    def setup_method(self):
        """Create fresh UniversalConnector instance for each test"""
        self.connector_manager = UniversalConnector()

    def test_initialization(self):
        """Test connector manager initialization"""
        assert self.connector_manager.connectors == {}
        assert len(self.connector_manager.connector_specs) > 0  # Built-in specs loaded

    def test_builtin_connectors_loaded(self):
        """Test that built-in connector specs are loaded"""
        assert "grants_gov" in self.connector_manager.connector_specs
        assert "foundation_center" in self.connector_manager.connector_specs
        assert "quickbooks" in self.connector_manager.connector_specs

    def test_builtin_connector_details(self):
        """Test details of a built-in connector"""
        grants_spec = self.connector_manager.connector_specs["grants_gov"]

        assert grants_spec.name == "grants_gov"
        assert grants_spec.connector_type == ConnectorType.GOVERNMENT
        assert grants_spec.authentication == AuthenticationType.API_KEY
        assert "search" in grants_spec.endpoints
        assert "requests_per_minute" in grants_spec.rate_limits

    def test_create_connector_with_credentials(self):
        """Test creating a connector with explicit credentials"""
        spec = self.connector_manager.connector_specs["grants_gov"]
        credentials = {"api_key": "test_key_123"}

        connector_id = self.connector_manager.create_connector(spec, credentials)

        assert connector_id in self.connector_manager.connectors
        connector = self.connector_manager.connectors[connector_id]
        assert connector.specification == spec
        assert connector.credentials["api_key"] == "test_key_123"
        assert connector.status == "active"

    def test_create_connector_from_env(self):
        """Test creating a connector with credentials from environment"""
        spec = self.connector_manager.connector_specs["grants_gov"]

        with patch.dict(os.environ, {"GRANTS_GOV_API_KEY": "env_key_456"}):
            connector_id = self.connector_manager.create_connector(spec)

            connector = self.connector_manager.connectors[connector_id]
            assert connector.credentials.get("api_key") == "env_key_456"

    def test_create_connector_oauth_not_implemented(self):
        """Test that OAuth connectors raise NotImplementedError"""
        spec = self.connector_manager.connector_specs["quickbooks"]

        connector_id = self.connector_manager.create_connector(spec)

        connector = self.connector_manager.connectors[connector_id]
        assert connector.status == "error"

    def test_create_connector_api_key_missing(self):
        """Test creating API key connector without credentials fails gracefully"""
        spec = self.connector_manager.connector_specs["grants_gov"]

        with patch.dict(os.environ, clear=True):
            connector_id = self.connector_manager.create_connector(spec, {})

            connector = self.connector_manager.connectors[connector_id]
            assert connector.status == "error"

    def test_create_connector_basic_auth(self):
        """Test creating a connector with basic authentication"""
        spec = ConnectorSpecification(
            name="test_basic",
            description="Test basic auth",
            connector_type=ConnectorType.API,
            base_url="https://api.example.com",
            authentication=AuthenticationType.BASIC,
            endpoints={"test": "/test"},
            parameters={},
            rate_limits={"requests_per_minute": 60},
            capabilities=["test"]
        )

        credentials = {"username": "testuser", "password": "testpass"}
        connector_id = self.connector_manager.create_connector(spec, credentials)

        connector = self.connector_manager.connectors[connector_id]
        assert connector.status == "active"

    def test_create_connector_none_auth(self):
        """Test creating a connector with no authentication"""
        spec = ConnectorSpecification(
            name="test_none",
            description="Test no auth",
            connector_type=ConnectorType.API,
            base_url="https://api.example.com",
            authentication=AuthenticationType.NONE,
            endpoints={"test": "/test"},
            parameters={},
            rate_limits={"requests_per_minute": 60},
            capabilities=["test"]
        )

        connector_id = self.connector_manager.create_connector(spec)

        connector = self.connector_manager.connectors[connector_id]
        assert connector.status == "active"

    def test_get_connector_status_success(self):
        """Test getting connector status"""
        spec = self.connector_manager.connector_specs["grants_gov"]
        credentials = {"api_key": "test_key"}
        connector_id = self.connector_manager.create_connector(spec, credentials)

        status = self.connector_manager.get_connector_status(connector_id)

        assert status is not None
        assert status["id"] == connector_id
        assert status["name"] == "grants_gov"
        assert status["type"] == "government"
        assert status["status"] == "active"
        assert "capabilities" in status

    def test_get_connector_status_not_found(self):
        """Test getting status of non-existent connector"""
        status = self.connector_manager.get_connector_status("non-existent-id")
        assert status is None

    @patch('universal_connector.requests.get')
    def test_execute_operation_success(self, mock_get):
        """Test executing an operation successfully"""
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        spec = self.connector_manager.connector_specs["grants_gov"]
        credentials = {"api_key": "test_key"}
        connector_id = self.connector_manager.create_connector(spec, credentials)

        result = self.connector_manager.execute_operation(
            connector_id,
            "search",
            {"query": "elder care"}
        )

        assert result["success"] is True
        assert "results" in result["data"]

    def test_execute_operation_connector_not_found(self):
        """Test executing operation on non-existent connector"""
        result = self.connector_manager.execute_operation(
            "non-existent-id",
            "search",
            {}
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_execute_operation_unknown_operation(self):
        """Test executing an unknown operation"""
        spec = self.connector_manager.connector_specs["grants_gov"]
        credentials = {"api_key": "test_key"}
        connector_id = self.connector_manager.create_connector(spec, credentials)

        result = self.connector_manager.execute_operation(
            connector_id,
            "unknown_operation",
            {}
        )

        assert result["success"] is False
        assert "Unknown operation" in result["error"]

    @patch('universal_connector.requests.get')
    def test_execute_operation_updates_metrics(self, mock_get):
        """Test that executing operation updates usage metrics"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        spec = self.connector_manager.connector_specs["grants_gov"]
        credentials = {"api_key": "test_key"}
        connector_id = self.connector_manager.create_connector(spec, credentials)

        initial_usage = self.connector_manager.connectors[connector_id].usage_count

        self.connector_manager.execute_operation(connector_id, "search", {})

        assert self.connector_manager.connectors[connector_id].usage_count == initial_usage + 1

    def test_rate_limiting_per_minute(self):
        """Test that rate limiting works per minute"""
        spec = ConnectorSpecification(
            name="rate_test",
            description="Test rate limiting",
            connector_type=ConnectorType.API,
            base_url="https://api.example.com",
            authentication=AuthenticationType.NONE,
            endpoints={"test": "/test"},
            parameters={},
            rate_limits={"requests_per_minute": 2, "requests_per_hour": 100},
            capabilities=["test"]
        )

        connector_id = self.connector_manager.create_connector(spec)

        with patch('universal_connector.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {}
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # First two requests should succeed
            result1 = self.connector_manager.execute_operation(connector_id, "test", {})
            result2 = self.connector_manager.execute_operation(connector_id, "test", {})

            assert result1["success"] is True
            assert result2["success"] is True

            # Third request should fail due to rate limit
            result3 = self.connector_manager.execute_operation(connector_id, "test", {})
            assert result3["success"] is False
            assert "rate limit" in result3["error"].lower()

    @patch('universal_connector.requests.get')
    def test_http_error_handling(self, mock_get):
        """Test handling of HTTP errors"""
        import requests

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.side_effect = requests.HTTPError(response=mock_response)

        spec = self.connector_manager.connector_specs["grants_gov"]
        credentials = {"api_key": "test_key"}
        connector_id = self.connector_manager.create_connector(spec, credentials)

        result = self.connector_manager.execute_operation(connector_id, "search", {})

        assert result["success"] is False
        assert "HTTP" in result["error"]

    def test_get_connector_insights_empty(self):
        """Test insights with no connectors"""
        insights = self.connector_manager.get_connector_insights()

        assert insights["total_connectors"] == 0
        assert "configuration" in str(insights["recommendations"])

    def test_get_connector_insights_with_connectors(self):
        """Test insights with multiple connectors"""
        spec1 = self.connector_manager.connector_specs["grants_gov"]
        spec2 = self.connector_manager.connector_specs["foundation_center"]

        self.connector_manager.create_connector(spec1, {"api_key": "key1"})
        self.connector_manager.create_connector(spec2, {"api_key": "key2"})

        insights = self.connector_manager.get_connector_insights()

        assert insights["total_connectors"] == 2
        assert insights["connectors_by_type"]["government"] == 1
        assert insights["connectors_by_type"]["foundation"] == 1
        assert len(insights["recently_used"]) == 2

    def test_get_connector_insights_low_success_rate(self):
        """Test that low success rate triggers recommendations"""
        spec = self.connector_manager.connector_specs["grants_gov"]
        connector_id = self.connector_manager.create_connector(spec, {"api_key": "key"})

        # Manually set a low success rate to test the recommendation logic
        connector = self.connector_manager.connectors[connector_id]
        connector.success_rate = 0.3  # Set to below 0.5 threshold
        connector.usage_count = 10  # Ensure it has been used

        insights = self.connector_manager.get_connector_insights()

        # Verify the connector has low success rate
        assert connector.success_rate < 0.5

        # Should have low success rate recommendation
        assert any("low success" in rec["message"].lower()
                  for rec in insights["recommendations"])

    def test_cleanup_inactive_connectors(self):
        """Test cleanup of inactive connectors"""
        spec = self.connector_manager.connector_specs["grants_gov"]
        connector_id = self.connector_manager.create_connector(spec, {"api_key": "key"})

        # Manually set last_used to a very old timestamp
        import time
        old_time = datetime.fromtimestamp(time.time() - 48 * 3600)  # 48 hours ago
        self.connector_manager.connectors[connector_id].last_used = old_time

        removed = self.connector_manager.cleanup_inactive_connectors(inactive_hours=24)

        assert removed == 1
        assert connector_id not in self.connector_manager.connectors

    def test_cleanup_keeps_active_connectors(self):
        """Test that active connectors are not cleaned up"""
        spec = self.connector_manager.connector_specs["grants_gov"]
        connector_id = self.connector_manager.create_connector(spec, {"api_key": "key"})

        removed = self.connector_manager.cleanup_inactive_connectors(inactive_hours=24)

        assert removed == 0
        assert connector_id in self.connector_manager.connectors


class TestGlobalInstance:
    """Test the global universal_connector instance"""

    def test_global_instance_exists(self):
        """Test that global instance is available"""
        assert universal_connector is not None
        assert isinstance(universal_connector, UniversalConnector)

    def test_global_instance_has_builtin_specs(self):
        """Test that global instance has built-in connector specs"""
        assert len(universal_connector.connector_specs) > 0
        assert "grants_gov" in universal_connector.connector_specs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
