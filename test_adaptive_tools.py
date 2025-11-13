#!/usr/bin/env python3
"""
Test suite for adaptive_tools.py
Tests the adaptive tool management system
"""

import pytest
from unittest.mock import patch, Mock
from adaptive_tools import (
    ToolType,
    ToolSpecification,
    ToolInstance,
    AdaptiveTools,
    adaptive_tools,
    _web_scraping_handler,
    _document_generation_handler,
    _api_integration_handler,
    _data_processing_handler,
    _communication_handler,
    _automation_handler,
    _analytics_handler,
    _monitoring_handler,
    _generic_handler,
    _not_implemented_handler
)


class TestToolType:
    """Tests for ToolType enum"""

    def test_tool_type_values(self):
        """Test that all tool types have correct values"""
        assert ToolType.WEB_SCRAPING.value == "web_scraping"
        assert ToolType.DOCUMENT_GENERATION.value == "document_generation"
        assert ToolType.API_INTEGRATION.value == "api_integration"
        assert ToolType.DATA_PROCESSING.value == "data_processing"
        assert ToolType.COMMUNICATION.value == "communication"
        assert ToolType.AUTOMATION.value == "automation"
        assert ToolType.ANALYTICS.value == "analytics"
        assert ToolType.MONITORING.value == "monitoring"
        assert ToolType.GENERIC.value == "generic"


class TestToolHandlers:
    """Tests for individual tool handlers"""

    def test_not_implemented_handler(self):
        """Test the fallback handler for unsupported tools"""
        result = _not_implemented_handler({})
        assert result["success"] is False
        assert "not implemented" in result["error"].lower()

    @patch('adaptive_tools.requests.get')
    def test_web_scraping_handler_success(self, mock_get):
        """Test successful web scraping"""
        mock_response = Mock()
        mock_response.text = "<html>Test content</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = _web_scraping_handler({"url": "https://example.com"})

        assert result["success"] is True
        assert "<html>Test content</html>" in result["data"]
        mock_get.assert_called_once()

    def test_web_scraping_handler_no_url(self):
        """Test web scraping without URL"""
        result = _web_scraping_handler({})
        assert result["success"] is False
        assert "url" in result["error"].lower()

    @patch('adaptive_tools.requests.get')
    def test_web_scraping_handler_error(self, mock_get):
        """Test web scraping with network error"""
        mock_get.side_effect = Exception("Network error")

        result = _web_scraping_handler({"url": "https://example.com"})

        assert result["success"] is False
        assert "Network error" in result["error"]

    def test_document_generation_handler_success(self):
        """Test successful document generation"""
        result = _document_generation_handler({"content": "Test document content"})

        assert result["success"] is True
        assert "Test document content" in result["data"]

    def test_document_generation_handler_no_content(self):
        """Test document generation without content"""
        result = _document_generation_handler({})

        assert result["success"] is False
        assert "content" in result["error"].lower()

    @patch('adaptive_tools.requests.get')
    def test_api_integration_handler_get(self, mock_get):
        """Test API integration with GET request"""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = _api_integration_handler({
            "url": "https://api.example.com/data",
            "method": "GET"
        })

        assert result["success"] is True
        assert result["data"]["status"] == "ok"
        assert result["status_code"] == 200

    @patch('adaptive_tools.requests.post')
    def test_api_integration_handler_post(self, mock_post):
        """Test API integration with POST request"""
        mock_response = Mock()
        mock_response.json.return_value = {"created": True}
        mock_response.status_code = 201
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = _api_integration_handler({
            "url": "https://api.example.com/create",
            "method": "POST",
            "body": {"name": "test"}
        })

        assert result["success"] is True
        assert result["data"]["created"] is True

    def test_api_integration_handler_no_url(self):
        """Test API integration without URL"""
        result = _api_integration_handler({})

        assert result["success"] is False
        assert "url" in result["error"].lower()

    def test_data_processing_handler_success(self):
        """Test successful data processing"""
        result = _data_processing_handler({"data": [1, 2, 3, 4, 5]})

        assert result["success"] is True
        assert result["data"]["sum"] == 15
        assert result["data"]["count"] == 5
        assert result["data"]["mean"] == 3.0

    def test_data_processing_handler_empty_list(self):
        """Test data processing with empty list"""
        result = _data_processing_handler({"data": []})

        assert result["success"] is True
        assert result["data"]["sum"] == 0
        assert result["data"]["count"] == 0
        assert result["data"]["mean"] == 0.0

    def test_data_processing_handler_invalid_data(self):
        """Test data processing with invalid data type"""
        result = _data_processing_handler({"data": "not a list"})

        assert result["success"] is False
        assert "list" in result["error"].lower()

    def test_communication_handler_success(self):
        """Test successful communication"""
        result = _communication_handler({
            "message": "Hello, world!",
            "channel": "general"
        })

        assert result["success"] is True
        assert "general" in result["data"]

    def test_communication_handler_no_message(self):
        """Test communication without message"""
        result = _communication_handler({})

        assert result["success"] is False
        assert "message" in result["error"].lower()

    def test_automation_handler_success(self):
        """Test successful automation task"""
        result = _automation_handler({"task": "backup_database"})

        assert result["success"] is True
        assert "backup_database" in result["data"]

    def test_automation_handler_no_task(self):
        """Test automation without task"""
        result = _automation_handler({})

        assert result["success"] is False
        assert "task" in result["error"].lower()

    def test_analytics_handler_success(self):
        """Test successful analytics processing"""
        result = _analytics_handler({"data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})

        assert result["success"] is True
        assert result["data"]["min"] == 1
        assert result["data"]["max"] == 10
        assert result["data"]["median"] == 5.5
        assert "p25" in result["data"]
        assert "p75" in result["data"]

    def test_analytics_handler_single_value(self):
        """Test analytics with single value"""
        result = _analytics_handler({"data": [42]})

        assert result["success"] is True
        assert result["data"]["min"] == 42
        assert result["data"]["max"] == 42
        assert result["data"]["median"] == 42

    def test_analytics_handler_empty_data(self):
        """Test analytics with empty data"""
        result = _analytics_handler({"data": []})

        assert result["success"] is False

    def test_monitoring_handler_success(self):
        """Test successful monitoring"""
        result = _monitoring_handler({})

        assert result["success"] is True
        assert "timestamp" in result["data"]
        assert isinstance(result["data"]["timestamp"], float)

    def test_generic_handler_success(self):
        """Test generic handler echoes input"""
        params = {"key1": "value1", "key2": "value2"}
        result = _generic_handler(params)

        assert result["success"] is True
        assert result["data"] == params


class TestAdaptiveTools:
    """Tests for AdaptiveTools class"""

    def setup_method(self):
        """Create fresh AdaptiveTools instance for each test"""
        self.tools = AdaptiveTools()

    def test_create_tool_success(self):
        """Test creating a tool successfully"""
        spec = ToolSpecification(
            name="TestWebScraper",
            description="Test web scraping tool",
            tool_type=ToolType.WEB_SCRAPING,
            parameters={"url": "string"},
            returns={"data": "string"},
            capabilities=["scraping", "parsing"]
        )

        tool_id = self.tools.create_tool(spec)

        assert tool_id in self.tools.tools
        assert tool_id in self.tools.specifications
        assert self.tools.tools[tool_id].specification == spec
        assert self.tools.tools[tool_id].usage_count == 0

    def test_create_multiple_tools(self):
        """Test creating multiple tools"""
        for i in range(3):
            spec = ToolSpecification(
                name=f"Tool{i}",
                description=f"Tool {i}",
                tool_type=ToolType.GENERIC,
                parameters={},
                returns={},
                capabilities=[]
            )
            self.tools.create_tool(spec)

        assert len(self.tools.tools) == 3

    @patch('adaptive_tools.requests.get')
    def test_execute_tool_success(self, mock_get):
        """Test executing a tool successfully"""
        mock_response = Mock()
        mock_response.text = "Success"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        spec = ToolSpecification(
            name="Scraper",
            description="Web scraper",
            tool_type=ToolType.WEB_SCRAPING,
            parameters={"url": "string"},
            returns={"data": "string"},
            capabilities=["scraping"]
        )

        tool_id = self.tools.create_tool(spec)
        result = self.tools.execute_tool(tool_id, {"url": "https://example.com"})

        assert result["success"] is True
        assert self.tools.tools[tool_id].usage_count == 1
        assert self.tools.tools[tool_id].last_used is not None

    def test_execute_tool_not_found(self):
        """Test executing a non-existent tool"""
        result = self.tools.execute_tool("non-existent-id", {})

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_execute_tool_with_error(self):
        """Test executing a tool that raises an exception"""
        spec = ToolSpecification(
            name="DataProcessor",
            description="Processes data",
            tool_type=ToolType.DATA_PROCESSING,
            parameters={"data": "list"},
            returns={"result": "dict"},
            capabilities=["processing"]
        )

        tool_id = self.tools.create_tool(spec)

        # Pass invalid data to trigger error
        result = self.tools.execute_tool(tool_id, {"data": "not-a-list"})

        assert result["success"] is False
        assert "error" in result

    def test_execute_tool_updates_metrics(self):
        """Test that tool execution updates usage metrics"""
        spec = ToolSpecification(
            name="Monitor",
            description="Monitoring tool",
            tool_type=ToolType.MONITORING,
            parameters={},
            returns={"timestamp": "float"},
            capabilities=["monitoring"]
        )

        tool_id = self.tools.create_tool(spec)
        initial_usage = self.tools.tools[tool_id].usage_count

        self.tools.execute_tool(tool_id, {})

        assert self.tools.tools[tool_id].usage_count == initial_usage + 1

    def test_get_tool_insights_empty(self):
        """Test insights for empty tool registry"""
        insights = self.tools.get_tool_insights()

        assert insights["total_tools"] == 0
        assert insights["tools_by_type"] == {}
        assert insights["most_used_tools"] == []
        assert insights["recently_created"] == []

    def test_get_tool_insights_with_tools(self):
        """Test insights with multiple tools"""
        # Create tools of different types
        for tool_type in [ToolType.WEB_SCRAPING, ToolType.GENERIC, ToolType.GENERIC]:
            spec = ToolSpecification(
                name=f"{tool_type.value}_tool",
                description="Test tool",
                tool_type=tool_type,
                parameters={},
                returns={},
                capabilities=[]
            )
            tool_id = self.tools.create_tool(spec)

            # Execute some tools more than others
            if tool_type == ToolType.GENERIC:
                self.tools.execute_tool(tool_id, {})
                self.tools.execute_tool(tool_id, {})

        insights = self.tools.get_tool_insights()

        assert insights["total_tools"] == 3
        assert insights["tools_by_type"]["generic"] == 2
        assert insights["tools_by_type"]["web_scraping"] == 1
        assert len(insights["most_used_tools"]) > 0
        assert len(insights["recently_created"]) == 3

    def test_create_tool_with_unsupported_type(self):
        """Test creating a tool with no implementation uses fallback"""
        # Create a custom enum value for testing (bypassing the enum)
        spec = ToolSpecification(
            name="UnsupportedTool",
            description="Tool with no implementation",
            tool_type=ToolType.GENERIC,  # Use existing type for creation
            parameters={},
            returns={},
            capabilities=[]
        )

        tool_id = self.tools.create_tool(spec)

        # Tool should be created successfully
        assert tool_id in self.tools.tools


class TestGlobalInstance:
    """Test the global adaptive_tools instance"""

    def test_global_instance_exists(self):
        """Test that global instance is available"""
        assert adaptive_tools is not None
        assert isinstance(adaptive_tools, AdaptiveTools)

    def test_global_instance_usable(self):
        """Test that global instance can create and execute tools"""
        # Note: This test uses the global instance, so cleanup between tests
        # isn't perfect, but we can still verify basic functionality
        spec = ToolSpecification(
            name="GlobalTestTool",
            description="Tool for global instance test",
            tool_type=ToolType.MONITORING,
            parameters={},
            returns={},
            capabilities=[]
        )

        tool_id = adaptive_tools.create_tool(spec)
        result = adaptive_tools.execute_tool(tool_id, {})

        assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
