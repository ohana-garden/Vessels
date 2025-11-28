#!/usr/bin/env python3
"""
Universal Connector – production‑ready implementation.

DEPRECATED: This module is superseded by the MCP Explorer and MCP Ambassadors.

The new architecture:
- MCP Explorer (vessels/agents/mcp_explorer.py) discovers external capabilities
- MCP Ambassadors (vessels/agents/mcp_ambassador.py) personify MCP servers
- Vessels have vessel-scoped connector_configs (vessels/core/vessel.py)
- External capabilities are MCP servers, not hardcoded connector types

Migration path:
    Old: universal_connector.connector_manager.execute(connector_type, action, params)
    New: agent_zero.mcp_explorer.find_servers_for_need("capability")
         agent_zero.talk_to_ambassador(server_id, "how do I use this?")

See: vessels/agents/mcp_explorer.py, vessels/agents/mcp_ambassador.py
"""

from __future__ import annotations

import warnings
warnings.warn(
    "universal_connector is deprecated. Use MCP Explorer via agent_zero.mcp_explorer instead.",
    DeprecationWarning,
    stacklevel=2
)

import os
import json
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional

import requests

logger = logging.getLogger(__name__)


class ConnectorType(Enum):
    GOVERNMENT = "government"
    FOUNDATION = "foundation"
    COMMUNITY = "community"
    FINANCIAL = "financial"
    DOCUMENT = "document"
    API = "api"
    DATABASE = "database"
    FILE = "file"


class AuthenticationType(Enum):
    NONE = "none"
    API_KEY = "api_key"
    OAUTH = "oauth"
    BASIC = "basic"
    CUSTOM = "custom"


@dataclass
class ConnectorSpecification:
    """
    Specification describing how to connect to an external system.
    """
    name: str
    description: str
    connector_type: ConnectorType
    base_url: str
    authentication: AuthenticationType
    endpoints: Dict[str, str]
    parameters: Dict[str, Any]
    rate_limits: Dict[str, int]
    capabilities: List[str]


@dataclass
class ConnectorInstance:
    """Active connector instance."""
    id: str
    specification: ConnectorSpecification
    credentials: Dict[str, str]
    session_data: Dict[str, Any]
    last_used: datetime
    usage_count: int
    success_rate: float
    status: str


class UniversalConnector:
    """
    Safe connector manager for external systems.

    The connector system preloads a set of built‑in specifications and allows
    creation of new connectors via configuration.  Credentials may be
    provided explicitly or read from environment variables following the
    convention ``<SPEC_NAME>_API_KEY`` for API key authentication.
    """

    def __init__(self) -> None:
        self.connectors: Dict[str, ConnectorInstance] = {}
        self.connector_specs: Dict[str, ConnectorSpecification] = {}
        self.rate_limiter: Dict[str, Dict[str, int]] = {}
        self._load_builtin_connectors()

    # ---------------------------------------------------------------------
    # Connector specification loading
    # ---------------------------------------------------------------------
    def _load_builtin_connectors(self) -> None:
        """Load built‑in connector specifications."""
        # For brevity, only a small subset of connectors are defined here.  In a
        # production environment these should be configurable via external
        # configuration files or a database.
        builtin_connectors: List[ConnectorSpecification] = [
            ConnectorSpecification(
                name="grants_gov",
                description="Grants.gov federal grant portal",
                connector_type=ConnectorType.GOVERNMENT,
                base_url="https://www.grants.gov",
                authentication=AuthenticationType.API_KEY,
                endpoints={
                    "search": "/search-grants",
                    "opportunity": "/opportunity",
                    "apply": "/apply",
                    "status": "/status",
                },
                parameters={
                    "search_terms": "string",
                    "funding_instrument": "string",
                    "eligibility": "string",
                    "category": "string",
                },
                rate_limits={
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                },
                capabilities=[
                    "grant_search",
                    "opportunity_details",
                    "application_submission",
                    "status_tracking",
                ],
            ),
            ConnectorSpecification(
                name="foundation_center",
                description="Foundation Center grant database",
                connector_type=ConnectorType.FOUNDATION,
                base_url="https://api.foundationcenter.org",
                authentication=AuthenticationType.API_KEY,
                endpoints={
                    "search": "/v2/search",
                    "foundation": "/v2/foundation",
                    "grant": "/v2/grant",
                    "trends": "/v2/trends",
                },
                parameters={
                    "query": "string",
                    "filters": "dict",
                    "format": "string",
                },
                rate_limits={
                    "requests_per_minute": 30,
                    "requests_per_hour": 500,
                },
                capabilities=[
                    "foundation_search",
                    "grant_history",
                    "funding_trends",
                    "organization_profiles",
                ],
            ),
            ConnectorSpecification(
                name="quickbooks",
                description="QuickBooks financial system",
                connector_type=ConnectorType.FINANCIAL,
                base_url="https://sandbox-quickbooks.api.intuit.com",
                authentication=AuthenticationType.OAUTH,
                endpoints={
                    "accounts": "/v3/company/{companyId}/account",
                    "bills": "/v3/company/{companyId}/bill",
                    "budgets": "/v3/company/{companyId}/budget",
                    "reports": "/v3/company/{companyId}/reports",
                },
                parameters={
                    "company_id": "string",
                    "access_token": "string",
                    "refresh_token": "string",
                },
                rate_limits={
                    "requests_per_minute": 100,
                    "requests_per_hour": 5000,
                },
                capabilities=[
                    "financial_tracking",
                    "budget_management",
                    "expense_reporting",
                    "grant_financials",
                ],
            ),
        ]
        for spec in builtin_connectors:
            self.connector_specs[spec.name] = spec

    # ---------------------------------------------------------------------
    # Connector management
    # ---------------------------------------------------------------------
    def create_connector(self, specification: ConnectorSpecification, credentials: Optional[Dict[str, str]] = None) -> str:
        """
        Create a connector instance from a specification.  Credentials may be
        provided explicitly; if omitted, environment variables are used for
        API key authentication.  Instances are stored in an in‑memory
        registry.
        """
        import uuid

        connector_id = str(uuid.uuid4())
        if credentials is None:
            credentials = {}
        # For API key authentication, attempt to read from environment
        if specification.authentication == AuthenticationType.API_KEY:
            env_key = os.getenv(f"{specification.name.upper()}_API_KEY")
            if env_key and "api_key" not in credentials:
                credentials["api_key"] = env_key
        instance = ConnectorInstance(
            id=connector_id,
            specification=specification,
            credentials=credentials,
            session_data={},
            last_used=datetime.now(),
            usage_count=0,
            success_rate=1.0,
            status="created",
        )
        # Perform authentication setup
        try:
            self._setup_authentication(instance)
            instance.status = "active"
            logger.info(f"Connector {specification.name} created (ID={connector_id})")
        except Exception as e:
            instance.status = "error"
            logger.error(f"Failed to initialize connector {specification.name}: {e}")
        self.connectors[connector_id] = instance
        return connector_id

    def _setup_authentication(self, connector: ConnectorInstance) -> None:
        """
        Placeholder for authentication setup.  For API key authentication the
        provided key is stored; for OAuth and other schemes an exception is
        raised since this implementation does not include full OAuth flows.
        """
        auth_type = connector.specification.authentication
        if auth_type == AuthenticationType.OAUTH:
            raise NotImplementedError("OAuth authentication requires external token management")
        elif auth_type == AuthenticationType.API_KEY:
            if not connector.credentials.get("api_key"):
                raise ValueError(f"API key missing for connector {connector.specification.name}")
        elif auth_type == AuthenticationType.BASIC:
            if not (connector.credentials.get("username") and connector.credentials.get("password")):
                raise ValueError(f"Username/password missing for connector {connector.specification.name}")
        # NONE or CUSTOM do not require setup here
        return None

    def get_connector_status(self, connector_id: str) -> Optional[Dict[str, Any]]:
        """Return the status of a connector by ID."""
        connector = self.connectors.get(connector_id)
        if not connector:
            return None
        return {
            "id": connector.id,
            "name": connector.specification.name,
            "type": connector.specification.connector_type.value,
            "status": connector.status,
            "usage_count": connector.usage_count,
            "success_rate": connector.success_rate,
            "last_used": connector.last_used.isoformat(),
            "capabilities": connector.specification.capabilities,
        }

    def execute_operation(self, connector_id: str, operation: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an operation on a connector.  Rate limits are respected based
        on the connector's specification.  Returns a dictionary containing
        ``success`` and either ``data`` or ``error``.
        """
        if parameters is None:
            parameters = {}
        connector = self.connectors.get(connector_id)
        if not connector:
            return {"success": False, "error": "Connector not found"}
        # Check rate limit
        if not self._check_rate_limit(connector, operation):
            return {"success": False, "error": "Rate limit exceeded"}
        endpoint = connector.specification.endpoints.get(operation)
        if not endpoint:
            return {"success": False, "error": f"Unknown operation '{operation}' for {connector.specification.name}"}
        try:
            result = self._make_request(connector, endpoint, parameters)
            # Update success rate statistics
            connector.usage_count += 1
            connector.last_used = datetime.now()
            if result.get("success"):
                # Weighted moving average for success rate
                connector.success_rate = ((connector.success_rate * (connector.usage_count - 1)) + 1) / connector.usage_count
            else:
                connector.success_rate = (connector.success_rate * (connector.usage_count - 1)) / connector.usage_count
            return result
        except Exception as e:
            logger.error(f"Error executing operation {operation} on {connector.specification.name}: {e}")
            return {"success": False, "error": str(e)}

    def _check_rate_limit(self, connector: ConnectorInstance, operation: str) -> bool:
        """
        Enforce per‑minute and per‑hour rate limits defined in the connector
        specification.  Returns True if the operation may proceed; False
        otherwise.
        """
        now = time.time()
        rid = connector.id
        if rid not in self.rate_limiter:
            self.rate_limiter[rid] = {}
        limits = self.rate_limiter[rid]
        minute_key = int(now // 60)
        hour_key = int(now // 3600)
        # Initialize counters for current buckets
        limits.setdefault(minute_key, 0)
        limits.setdefault(hour_key, 0)
        spec_limits = connector.specification.rate_limits
        minute_limit = spec_limits.get("requests_per_minute", 60)
        hour_limit = spec_limits.get("requests_per_hour", 1000)
        if limits[minute_key] >= minute_limit or limits[hour_key] >= hour_limit:
            return False
        limits[minute_key] += 1
        limits[hour_key] += 1
        return True

    def _make_request(self, connector: ConnectorInstance, endpoint: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an HTTP GET request to the given endpoint.  Handles API key
        authentication and returns a standardized response structure.  The
        method can be extended to support POST, PUT, DELETE as needed.
        """
        url = connector.specification.base_url.rstrip("/") + endpoint
        headers: Dict[str, str] = {
            "User-Agent": "Vessels-Universal-Connector/2.0",
            "Accept": "application/json",
        }
        # API key authentication
        if connector.specification.authentication == AuthenticationType.API_KEY:
            api_key = connector.credentials.get("api_key")
            if api_key:
                # Use Bearer token by default; override in spec if needed
                headers["Authorization"] = f"Bearer {api_key}"
        elif connector.specification.authentication == AuthenticationType.BASIC:
            import base64
            auth_str = f"{connector.credentials.get('username')}:{connector.credentials.get('password')}"
            headers["Authorization"] = "Basic " + base64.b64encode(auth_str.encode()).decode()
        # Make request
        try:
            response = requests.get(url, headers=headers, params=parameters, timeout=30)
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError:
                data = response.text
            return {"success": True, "data": data, "status_code": response.status_code}
        except requests.HTTPError as e:
            # Capture non‑2xx responses
            status = e.response.status_code if hasattr(e, "response") else 0
            text = e.response.text if hasattr(e, "response") else str(e)
            logger.warning(f"HTTP error {status} for {url}: {text}")
            return {"success": False, "error": f"HTTP {status}: {text}", "status_code": status}
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
            return {"success": False, "error": f"Request failed: {e}"}

    # ---------------------------------------------------------------------
    # Connector insights and cleanup
    # ---------------------------------------------------------------------
    def get_connector_insights(self) -> Dict[str, Any]:
        """
        Return summary metrics for all connectors, including usage and success
        statistics.  Recommendations are provided when usage is low or
        success rates drop below 50%.
        """
        insights = {
            "total_connectors": len(self.connectors),
            "connectors_by_type": {},
            "most_used_connectors": [],
            "highest_success_rate": [],
            "recently_used": [],
            "recommendations": [],
        }
        # Count by type and collect sorting data
        for conn in self.connectors.values():
            ctype = conn.specification.connector_type.value
            insights["connectors_by_type"][ctype] = insights["connectors_by_type"].get(ctype, 0) + 1
        sorted_by_usage = sorted(self.connectors.values(), key=lambda c: c.usage_count, reverse=True)
        insights["most_used_connectors"] = [
            {"name": c.specification.name, "usage_count": c.usage_count}
            for c in sorted_by_usage[:5]
        ]
        sorted_by_success = sorted(self.connectors.values(), key=lambda c: c.success_rate, reverse=True)
        insights["highest_success_rate"] = [
            {"name": c.specification.name, "success_rate": c.success_rate}
            for c in sorted_by_success[:5]
        ]
        sorted_by_recent = sorted(self.connectors.values(), key=lambda c: c.last_used, reverse=True)
        insights["recently_used"] = [
            {"name": c.specification.name, "last_used": c.last_used.isoformat()}
            for c in sorted_by_recent[:5]
        ]
        # Recommendations
        if not self.connectors:
            insights["recommendations"].append({
                "type": "configuration",
                "message": "No connectors configured. Configure connectors to enable functionality.",
            })
        low_success = [c for c in self.connectors.values() if c.success_rate < 0.5]
        if low_success:
            insights["recommendations"].append({
                "type": "maintenance",
                "message": f"{len(low_success)} connectors have low success rates (<50%). Investigate endpoints and credentials.",
            })
        return insights

    def cleanup_inactive_connectors(self, inactive_hours: int = 24) -> int:
        """
        Remove connectors that have not been used for a specified number of
        hours.  Returns the number of connectors removed.
        """
        cutoff = datetime.now().timestamp() - inactive_hours * 3600
        to_remove = [cid for cid, conn in self.connectors.items() if conn.last_used.timestamp() < cutoff]
        for cid in to_remove:
            del self.connectors[cid]
            if cid in self.rate_limiter:
                del self.rate_limiter[cid]
        logger.info(f"Removed {len(to_remove)} inactive connectors")
        return len(to_remove)


# Provide a global instance
universal_connector = UniversalConnector()
