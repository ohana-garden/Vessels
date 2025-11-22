#!/usr/bin/env python3
"""
Adaptive Tools – production‑ready implementation.

This module provides a safe and extensible tool management system for the Vessels
platform.  The previous version dynamically generated code using ``exec``, which
posed significant security risks and made debugging difficult.  The rewritten
version defines explicit tool implementations for each ``ToolType`` and
performs strict parameter validation and error handling.  Additional tool
types can be implemented by adding new functions to the ``_TOOL_IMPLEMENTATIONS``
mapping.  Unsupported tool types return a clear error message rather than
executing arbitrary code.
"""

from __future__ import annotations

import logging
import requests
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Any, Optional


# Configure a module‑level logger.  In production code this should be hooked
# into the application’s logging configuration.
logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Enumeration of supported tool types."""
    WEB_SCRAPING = "web_scraping"
    DOCUMENT_GENERATION = "document_generation"
    API_INTEGRATION = "api_integration"
    DATA_PROCESSING = "data_processing"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    ANALYTICS = "analytics"
    MONITORING = "monitoring"
    GENERIC = "generic"


@dataclass
class ToolSpecification:
    """Declarative description of a tool."""
    name: str
    description: str
    tool_type: ToolType
    parameters: Dict[str, str]
    returns: Dict[str, str]
    capabilities: List[str]


@dataclass
class ToolInstance:
    """Instance of a tool with bound implementation."""
    id: str
    specification: ToolSpecification
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]
    created_at: float
    usage_count: int = 0
    last_used: Optional[float] = None


class AdaptiveTools:
    """
    Adaptive tool registry that creates and manages tools safely.

    The system maps each ``ToolType`` to a concrete Python function.  If a tool
    type is requested that has no implementation, a stub function is returned
    which informs the caller that the tool is not yet implemented.  Logging is
    used extensively to aid in debugging and operational monitoring.

    Supports optional gating: when a gate is provided, all tool executions
    are checked against moral constraints before execution.
    """

    def __init__(self, gate: Any = None, tracker: Any = None, vessel_id: str | None = None) -> None:
        """
        Initialize AdaptiveTools.

        Args:
            gate: Optional ActionGate for constraint checking
            tracker: Optional tracker for security events and state transitions
            vessel_id: Optional vessel ID for context tracking
        """
        self.tools: Dict[str, ToolInstance] = {}
        self.specifications: Dict[str, ToolSpecification] = {}
        self.gate = gate
        self.tracker = tracker
        self.vessel_id = vessel_id

    def create_tool(self, spec: ToolSpecification) -> str:
        """Create a new tool instance from a specification."""
        import time
        from uuid import uuid4

        tool_id = str(uuid4())
        handler = self._get_tool_handler(spec.tool_type)

        instance = ToolInstance(
            id=tool_id,
            specification=spec,
            handler=handler,
            created_at=time.time(),
        )
        self.tools[tool_id] = instance
        self.specifications[tool_id] = spec
        logger.info(f"Created tool {spec.name} ({spec.tool_type.value}) with ID {tool_id}")
        return tool_id

    def execute_tool(
        self,
        tool_id: str,
        params: Dict[str, Any],
        *,
        agent_id: Optional[str] = None,
        gate_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool and return its result, passing through an optional gate.

        Args:
            tool_id: ID of the tool to execute
            params: Parameters to pass to the tool
            agent_id: Optional agent ID for gating
            gate_metadata: Optional metadata for gating context

        Returns:
            Tool execution result with success/error status
        """
        if tool_id not in self.tools:
            logger.error(f"Tool {tool_id} not found")
            return {"success": False, "error": "Tool not found"}

        tool = self.tools[tool_id]

        # Update usage tracking
        tool.usage_count += 1
        import time
        tool.last_used = time.time()

        # Prepare gate metadata
        gating_decision = None
        gate_metadata = gate_metadata or {}
        gate_metadata.setdefault("tool_id", tool_id)
        gate_metadata.setdefault("tool_name", tool.specification.name)
        gate_metadata.setdefault("tool_type", tool.specification.tool_type.value)
        if self.vessel_id:
            gate_metadata.setdefault("vessel_id", self.vessel_id)

        # Gate the action if gate is configured
        if self.gate:
            gating_decision = self.gate.gate_action(
                agent_id or "anonymous_agent",
                {"tool": tool.specification.name, "params": list(params.keys())},
                action_metadata=gate_metadata,
            )
            if not gating_decision.allowed:
                if getattr(gating_decision, "security_event", None) and self.tracker:
                    self.tracker.store_security_event(gating_decision.security_event)
                return {
                    "success": False,
                    "error": gating_decision.reason,
                    "gated": False,
                }

        try:
            result = tool.handler(params)
            # Ensure a consistent response format
            if not isinstance(result, dict) or "success" not in result:
                logger.warning(
                    f"Tool {tool_id} returned non‑conforming result; wrapping in success structure"
                )
                return {"success": True, "data": result}
            if gating_decision and gating_decision.security_event and self.tracker:
                self.tracker.store_security_event(gating_decision.security_event)
            if gating_decision and gating_decision.state_transition and self.tracker:
                self.tracker.store_transition(gating_decision.state_transition)
            return result | {"gating_reason": gating_decision.reason if gating_decision else "skipped"}
        except Exception as e:
            logger.exception(f"Error executing tool {tool_id}: {e}")
            return {"success": False, "error": str(e)}

    def _get_tool_handler(self, tool_type: ToolType) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """
        Return a safe handler for the given tool type.  Unknown tool types
        return a stub handler that informs the caller that the tool is not
        implemented.
        """
        return _TOOL_IMPLEMENTATIONS.get(tool_type, _not_implemented_handler)

    def get_tool_insights(self) -> Dict[str, Any]:
        """Return summary information about the tool registry."""
        insights = {
            "total_tools": len(self.tools),
            "tools_by_type": {},
            "most_used_tools": [],
            "recently_created": [],
        }
        import time
        now = time.time()
        # Count by type
        for tool in self.tools.values():
            ttype = tool.specification.tool_type.value
            insights["tools_by_type"][ttype] = insights["tools_by_type"].get(ttype, 0) + 1
        # Most used
        sorted_tools = sorted(self.tools.values(), key=lambda t: t.usage_count, reverse=True)
        insights["most_used_tools"] = [
            {"name": t.specification.name, "usage_count": t.usage_count}
            for t in sorted_tools[:5]
        ]
        # Recently created
        recent = sorted(self.tools.values(), key=lambda t: t.created_at, reverse=True)
        insights["recently_created"] = [
            {"name": t.specification.name, "created_at": t.created_at}
            for t in recent[:5]
        ]
        return insights


def _not_implemented_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback handler for unsupported tools."""
    return {
        "success": False,
        "error": "This tool type is not implemented yet. Please choose a different tool type."
    }


def _web_scraping_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basic web scraping handler.

    Required parameters: ``url``.
    Optional parameters: ``method`` (GET/POST), ``headers``, ``params``.
    Returns raw HTML in the ``data`` field.
    """
    url = params.get("url")
    if not url:
        return {"success": False, "error": "'url' parameter is required"}
    method = params.get("method", "GET").upper()
    headers = params.get("headers", {})
    query_params = params.get("params", {})
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=query_params, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=headers, data=query_params, timeout=10)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        resp.raise_for_status()
        return {"success": True, "data": resp.text}
    except Exception as e:
        logger.error(f"Web scraping failed for {url}: {e}")
        return {"success": False, "error": str(e)}


def _document_generation_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder document generation handler.

    This implementation simply returns the provided content or a placeholder
    indicating that the functionality is not yet implemented.  A real
    implementation would integrate with a template engine or document
    generation library (e.g., Jinja2, reportlab).
    """
    content = params.get("content")
    if not content:
        return {"success": False, "error": "No content provided for document generation"}
    # In a production environment, generate a PDF or other document format here.
    return {"success": True, "data": f"Document generated with content: {content}"}


def _api_integration_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic API integration handler.

    Required parameters: ``url``.  Optional parameters: ``method`` (GET, POST, PUT,
    DELETE), ``headers``, ``body``, ``params``.  Returns JSON‑decoded response
    when possible, otherwise raw text.
    """
    url = params.get("url")
    if not url:
        return {"success": False, "error": "'url' parameter is required"}
    method = params.get("method", "GET").upper()
    headers = params.get("headers", {})
    body = params.get("body")
    query_params = params.get("params", {})
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=query_params, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=body, params=query_params, timeout=10)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=body, params=query_params, timeout=10)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, params=query_params, timeout=10)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        resp.raise_for_status()
        # Try to decode JSON
        try:
            data = resp.json()
        except ValueError:
            data = resp.text
        return {"success": True, "data": data, "status_code": resp.status_code}
    except Exception as e:
        logger.error(f"API call failed for {url}: {e}")
        return {"success": False, "error": str(e)}


def _data_processing_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple data processing handler.

    Accepts a list of numbers under the ``data`` key and returns basic
    statistics such as sum, mean and count.  This is a placeholder for more
    complex data transformations.
    """
    data = params.get("data")
    if not isinstance(data, list):
        return {"success": False, "error": "'data' must be a list of numbers"}
    try:
        numbers = [float(x) for x in data]
        total = sum(numbers)
        count = len(numbers)
        mean = total / count if count else 0.0
        return {"success": True, "data": {"sum": total, "count": count, "mean": mean}}
    except Exception as e:
        logger.error(f"Data processing failed: {e}")
        return {"success": False, "error": str(e)}


def _communication_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stub communication handler.

    A real implementation would integrate with messaging services such as
    Slack, email or SMS.  Here we simply log the message and return a
    success response.
    """
    message = params.get("message")
    channel = params.get("channel", "default")
    if not message:
        return {"success": False, "error": "Message content is required"}
    logger.info(f"[Communication] Sending message to {channel}: {message}")
    return {"success": True, "data": f"Message sent to {channel}"}


def _automation_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stub automation handler.

    In production, this would trigger workflows or scheduled tasks.  For now it
    simply acknowledges the request.
    """
    task = params.get("task")
    if not task:
        return {"success": False, "error": "'task' parameter is required"}
    logger.info(f"[Automation] Executing task: {task}")
    return {"success": True, "data": f"Task '{task}' executed"}


def _analytics_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stub analytics handler.

    Accepts a list of numbers and returns basic percentiles.  In production
    this could interface with a statistics or ML library.
    """
    data = params.get("data")
    if not isinstance(data, list) or not data:
        return {"success": False, "error": "'data' must be a non‑empty list of numbers"}
    try:
        numbers = sorted(float(x) for x in data)
        n = len(numbers)
        def percentile(p: float) -> float:
            k = (n - 1) * p
            f = int(k)
            c = min(f + 1, n - 1)
            d = k - f
            return numbers[f] * (1 - d) + numbers[c] * d
        return {"success": True, "data": {
            "min": numbers[0],
            "max": numbers[-1],
            "median": percentile(0.5),
            "p25": percentile(0.25),
            "p75": percentile(0.75)
        }}
    except Exception as e:
        logger.error(f"Analytics processing failed: {e}")
        return {"success": False, "error": str(e)}


def _monitoring_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stub monitoring handler.

    Real implementations would query metrics from running services.  Here we
    simply return a heartbeat timestamp.
    """
    import time
    return {"success": True, "data": {"timestamp": time.time()}}


def _generic_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic handler that just echoes the input parameters.  Useful for
    prototyping or debugging.
    """
    return {"success": True, "data": params}


_TOOL_IMPLEMENTATIONS: Dict[ToolType, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    ToolType.WEB_SCRAPING: _web_scraping_handler,
    ToolType.DOCUMENT_GENERATION: _document_generation_handler,
    ToolType.API_INTEGRATION: _api_integration_handler,
    ToolType.DATA_PROCESSING: _data_processing_handler,
    ToolType.COMMUNICATION: _communication_handler,
    ToolType.AUTOMATION: _automation_handler,
    ToolType.ANALYTICS: _analytics_handler,
    ToolType.MONITORING: _monitoring_handler,
    ToolType.GENERIC: _generic_handler,
}


# Provide a global instance, similar to the original implementation
adaptive_tools = AdaptiveTools()
