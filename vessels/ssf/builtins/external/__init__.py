"""
External SSFs - MCP Tool Wrappers, HTTP Requests, Web Search.

These SSFs provide constrained access to external services,
ensuring all external interactions pass through the SSF safety layer.
"""

from typing import Dict, Any, List, Optional
from uuid import uuid4
import logging

from ...schema import (
    SSFDefinition,
    SSFCategory,
    RiskLevel,
    SSFHandler,
    ConstraintBindingConfig,
    ConstraintBindingMode,
    BoundaryBehavior,
)

logger = logging.getLogger(__name__)


# ============================================================================
# HANDLER IMPLEMENTATIONS
# ============================================================================

async def handle_mcp_tool_invoke(
    server_id: str,
    tool_name: str,
    arguments: Dict[str, Any],
    timeout_seconds: int = 30,
    **kwargs
) -> Dict[str, Any]:
    """
    Invoke an MCP tool through the SSF safety layer.

    Args:
        server_id: MCP server ID
        tool_name: Tool to invoke
        arguments: Tool arguments
        timeout_seconds: Maximum execution time

    Returns:
        Tool execution result
    """
    logger.info(f"MCP invoke: {server_id}/{tool_name}")

    # This would integrate with MCP client
    # Placeholder implementation
    return {
        "status": "invoked",
        "server_id": server_id,
        "tool_name": tool_name,
        "result": None,  # Would contain actual MCP result
    }


async def handle_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 30,
    **kwargs
) -> Dict[str, Any]:
    """
    Make an HTTP request through the SSF safety layer.

    Args:
        url: Request URL (must be HTTPS for external)
        method: HTTP method
        headers: Optional headers
        body: Optional request body
        timeout_seconds: Request timeout

    Returns:
        HTTP response
    """
    logger.info(f"HTTP {method}: {url}")

    # Validate URL safety
    if not url.startswith(('https://', 'http://localhost', 'http://127.0.0.1')):
        return {
            "status": "error",
            "error": "Only HTTPS or localhost URLs are allowed",
        }

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            request_headers = headers or {}
            if body:
                request_headers["Content-Type"] = "application/json"

            async with session.request(
                method=method,
                url=url,
                headers=request_headers,
                json=body if method in ["POST", "PUT", "PATCH"] else None,
                timeout=aiohttp.ClientTimeout(total=timeout_seconds),
            ) as response:
                try:
                    response_body = await response.json()
                except Exception:
                    response_body = await response.text()

                return {
                    "status": "success",
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "body": response_body,
                }

    except ImportError:
        return {
            "status": "error",
            "error": "aiohttp not available",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


async def handle_web_search(
    query: str,
    num_results: int = 5,
    safe_search: bool = True,
    language: str = "en",
    **kwargs
) -> Dict[str, Any]:
    """
    Perform a web search with safety filtering.

    Args:
        query: Search query
        num_results: Number of results
        safe_search: Enable safe search
        language: Result language

    Returns:
        Search results
    """
    logger.info(f"Web search: {query}")

    # Placeholder - would integrate with search API
    return {
        "query": query,
        "results": [],
        "result_count": 0,
        "safe_search": safe_search,
    }


async def handle_fetch_url_content(
    url: str,
    extract_text: bool = True,
    max_length: int = 10000,
    **kwargs
) -> Dict[str, Any]:
    """
    Fetch and extract content from a URL.

    Args:
        url: URL to fetch
        extract_text: Extract text content
        max_length: Maximum content length

    Returns:
        Fetched content
    """
    logger.info(f"Fetching content from: {url}")

    # Validate URL
    if not url.startswith(('https://', 'http://localhost', 'http://127.0.0.1')):
        return {
            "status": "error",
            "error": "Only HTTPS or localhost URLs are allowed",
        }

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status}",
                    }

                content = await response.text()

                # Truncate if needed
                if len(content) > max_length:
                    content = content[:max_length] + "..."

                return {
                    "status": "success",
                    "url": url,
                    "content": content,
                    "content_type": response.headers.get("Content-Type", ""),
                    "length": len(content),
                }

    except ImportError:
        return {
            "status": "error",
            "error": "aiohttp not available",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


# ============================================================================
# SSF DEFINITIONS
# ============================================================================

def _create_mcp_tool_invoke_ssf() -> SSFDefinition:
    """Create the mcp_tool_invoke SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="mcp_tool_invoke",
        version="1.0.0",
        category=SSFCategory.EXTERNAL_API,
        tags=["mcp", "tool", "external", "integration"],
        description="Invoke an MCP (Model Context Protocol) tool through the SSF safety layer.",
        description_for_llm="Use this SSF to invoke tools from MCP servers. Wraps MCP tool calls with constraint validation. Good for accessing external capabilities like weather, databases, or specialized services provided by MCP servers.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.external",
            function_name="handle_mcp_tool_invoke",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "string",
                    "description": "MCP server ID",
                },
                "tool_name": {
                    "type": "string",
                    "description": "Tool to invoke",
                },
                "arguments": {
                    "type": "object",
                    "description": "Tool arguments",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 30,
                    "description": "Execution timeout",
                },
            },
            "required": ["server_id", "tool_name", "arguments"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "server_id": {"type": "string"},
                "tool_name": {"type": "string"},
                "result": {},
            },
        },
        timeout_seconds=60,
        memory_mb=256,
        required_tools=["mcp_client"],
        risk_level=RiskLevel.MEDIUM,
        side_effects=[
            "Invokes external MCP tool",
            "May have tool-specific side effects",
        ],
        reversible=False,
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FULL,
            validate_inputs=True,
            validate_outputs=True,
            on_boundary_approach=BoundaryBehavior.ESCALATE,
        ),
    )


def _create_http_request_ssf() -> SSFDefinition:
    """Create the http_request SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="http_request",
        version="1.0.0",
        category=SSFCategory.EXTERNAL_API,
        tags=["http", "api", "request", "external", "rest"],
        description="Make HTTP requests to external APIs with safety constraints.",
        description_for_llm="Use this SSF to make HTTP requests to external APIs. Only HTTPS URLs are allowed for security. Supports GET, POST, PUT, DELETE methods. Good for integrating with REST APIs, webhooks, or external services.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.external",
            function_name="handle_http_request",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "format": "uri",
                    "description": "Request URL (HTTPS required)",
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                    "default": "GET",
                    "description": "HTTP method",
                },
                "headers": {
                    "type": "object",
                    "description": "Request headers",
                },
                "body": {
                    "type": "object",
                    "description": "Request body (for POST/PUT/PATCH)",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 30,
                    "description": "Request timeout",
                },
            },
            "required": ["url"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "status_code": {"type": "integer"},
                "headers": {"type": "object"},
                "body": {},
            },
        },
        timeout_seconds=60,
        memory_mb=256,
        risk_level=RiskLevel.MEDIUM,
        side_effects=[
            "Makes external HTTP request",
            "May expose data to external service",
        ],
        reversible=False,
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FULL,
            validate_inputs=True,
            validate_outputs=True,
            on_boundary_approach=BoundaryBehavior.BLOCK,
            forbidden_input_patterns=[
                r"(?i)password",
                r"(?i)secret",
                r"(?i)api.?key",
                r"(?i)bearer\s+",
            ],
        ),
    )


def _create_web_search_ssf() -> SSFDefinition:
    """Create the web_search SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="web_search",
        version="1.0.0",
        category=SSFCategory.EXTERNAL_API,
        tags=["search", "web", "internet", "lookup", "research"],
        description="Perform a web search with safety filtering enabled.",
        description_for_llm="Use this SSF to search the web for information. Safe search is enabled by default. Good for finding current information, researching topics, or looking up facts not in the knowledge base.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.external",
            function_name="handle_web_search",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Search query",
                },
                "num_results": {
                    "type": "integer",
                    "default": 5,
                    "maximum": 20,
                    "description": "Number of results",
                },
                "safe_search": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable safe search",
                },
                "language": {
                    "type": "string",
                    "default": "en",
                    "description": "Result language",
                },
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "results": {"type": "array"},
                "result_count": {"type": "integer"},
                "safe_search": {"type": "boolean"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.LOW,
        side_effects=[],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def _create_fetch_url_content_ssf() -> SSFDefinition:
    """Create the fetch_url_content SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="fetch_url_content",
        version="1.0.0",
        category=SSFCategory.EXTERNAL_API,
        tags=["fetch", "url", "content", "scrape", "web"],
        description="Fetch and extract content from a URL with safety constraints.",
        description_for_llm="Use this SSF to fetch content from web pages. Only HTTPS URLs are allowed. Good for reading articles, documentation, or web-based data. Content is truncated to prevent memory issues.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.external",
            function_name="handle_fetch_url_content",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL to fetch (HTTPS required)",
                },
                "extract_text": {
                    "type": "boolean",
                    "default": True,
                    "description": "Extract text content",
                },
                "max_length": {
                    "type": "integer",
                    "default": 10000,
                    "maximum": 50000,
                    "description": "Maximum content length",
                },
            },
            "required": ["url"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "url": {"type": "string"},
                "content": {"type": "string"},
                "content_type": {"type": "string"},
                "length": {"type": "integer"},
            },
        },
        timeout_seconds=45,
        memory_mb=512,
        risk_level=RiskLevel.LOW,
        side_effects=[],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def get_builtin_ssfs() -> List[SSFDefinition]:
    """Get all built-in external SSFs."""
    return [
        _create_mcp_tool_invoke_ssf(),
        _create_http_request_ssf(),
        _create_web_search_ssf(),
        _create_fetch_url_content_ssf(),
    ]
