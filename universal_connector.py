#!/usr/bin/env python3
"""
UNIVERSAL CONNECTOR SYSTEM
Connectors to EVERYTHING:
- Government grant portals
- Foundation databases
- Community platforms
- Financial systems
- Document repositories
- Make it connect to ANY system automatically
"""

import json
import logging
import sqlite3
import threading
import time
import requests
import urllib.parse
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod

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
    CERTIFICATE = "certificate"
    CUSTOM = "custom"

@dataclass
class ConnectorSpecification:
    """Specification for a connector"""
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
    """Active connector instance"""
    id: str
    specification: ConnectorSpecification
    credentials: Dict[str, str]
    session_data: Dict[str, Any]
    last_used: datetime
    usage_count: int
    success_rate: float
    status: str

class UniversalConnector:
    """Universal system connector that connects to any external system"""
    
    def __init__(self):
        self.connectors: Dict[str, ConnectorInstance] = {}
        self.connector_specs: Dict[str, ConnectorSpecification] = {}
        self.connection_pool: Dict[str, Any] = {}
        self.rate_limiter: Dict[str, Dict[str, float]] = {}
        self.auth_tokens: Dict[str, Dict[str, Any]] = {}
        self.session_manager = None
        
        self.initialize_connector_system()
    
    def initialize_connector_system(self):
        """Initialize the universal connector system"""
        # Load built-in connector specifications
        self._load_builtin_connectors()
        
        # Initialize session manager
        self.session_manager = self._create_session_manager()
        
        logger.info("Universal Connector System initialized")
    
    def _load_builtin_connectors(self):
        """Load built-in connector specifications"""
        builtin_connectors = [
            # Government Grant Portals
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
                    "status": "/status"
                },
                parameters={
                    "api_key": "string",
                    "search_terms": "string",
                    "funding_instrument": "string",
                    "eligibility": "string",
                    "category": "string"
                },
                rate_limits={
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000
                },
                capabilities=["grant_search", "opportunity_details", "application_submission", "status_tracking"]
            ),
            
            # Foundation Databases
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
                    "trends": "/v2/trends"
                },
                parameters={
                    "api_key": "string",
                    "query": "string",
                    "filters": "dict",
                    "format": "string"
                },
                rate_limits={
                    "requests_per_minute": 30,
                    "requests_per_hour": 500
                },
                capabilities=["foundation_search", "grant_history", "funding_trends", "organization_profiles"]
            ),
            
            # Hawaii Community Foundation
            ConnectorSpecification(
                name="hcf_grants",
                description="Hawaii Community Foundation grants",
                connector_type=ConnectorType.FOUNDATION,
                base_url="https://www.hawaiicommunityfoundation.org",
                authentication=AuthenticationType.NONE,
                endpoints={
                    "grants": "/grants",
                    "apply": "/apply",
                    "guidelines": "/guidelines",
                    "deadlines": "/deadlines"
                },
                parameters={
                    "category": "string",
                    "county": "string",
                    "deadline": "string"
                },
                rate_limits={
                    "requests_per_minute": 120,
                    "requests_per_hour": 2000
                },
                capabilities=["local_grant_search", "hawaii_specific", "community_focused", "deadline_tracking"]
            ),
            
            # Financial Systems
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
                    "reports": "/v3/company/{companyId}/reports"
                },
                parameters={
                    "company_id": "string",
                    "access_token": "string",
                    "refresh_token": "string"
                },
                rate_limits={
                    "requests_per_minute": 100,
                    "requests_per_hour": 5000
                },
                capabilities=["financial_tracking", "budget_management", "expense_reporting", "grant_financials"]
            ),
            
            # Document Management
            ConnectorSpecification(
                name="google_drive",
                description="Google Drive document storage",
                connector_type=ConnectorType.DOCUMENT,
                base_url="https://www.googleapis.com/drive/v3",
                authentication=AuthenticationType.OAUTH,
                endpoints={
                    "files": "/files",
                    "upload": "/files",
                    "permissions": "/files/{fileId}/permissions",
                    "sharing": "/files/{fileId}"
                },
                parameters={
                    "access_token": "string",
                    "folder_id": "string",
                    "file_name": "string"
                },
                rate_limits={
                    "requests_per_minute": 100,
                    "requests_per_hour": 10000
                },
                capabilities=["document_storage", "file_sharing", "collaboration", "version_control"]
            ),
            
            # Community Platforms
            ConnectorSpecification(
                name="slack",
                description="Slack communication platform",
                connector_type=ConnectorType.COMMUNITY,
                base_url="https://slack.com/api",
                authentication=AuthenticationType.API_KEY,
                endpoints={
                    "channels": "/conversations.list",
                    "messages": "/chat.postMessage",
                    "users": "/users.list",
                    "files": "/files.upload"
                },
                parameters={
                    "token": "string",
                    "channel": "string",
                    "message": "string"
                },
                rate_limits={
                    "requests_per_minute": 50,
                    "requests_per_hour": 1000
                },
                capabilities=["team_communication", "file_sharing", "notifications", "community_coordination"]
            ),
            
            # Database Connectors
            ConnectorSpecification(
                name="postgresql",
                description="PostgreSQL database",
                connector_type=ConnectorType.DATABASE,
                base_url="postgresql://localhost:5432",
                authentication=AuthenticationType.BASIC,
                endpoints={
                    "query": "/query",
                    "tables": "/tables",
                    "data": "/data"
                },
                parameters={
                    "host": "string",
                    "database": "string",
                    "username": "string",
                    "password": "string",
                    "query": "string"
                },
                rate_limits={
                    "requests_per_minute": 1000,
                    "requests_per_hour": 100000
                },
                capabilities=["data_storage", "query_execution", "data_retrieval", "backup_management"]
            )
        ]
        
        for spec in builtin_connectors:
            self.connector_specs[spec.name] = spec
    
    def _create_session_manager(self):
        """Create session manager for connections"""
        return {
            "sessions": {},
            "session_timeout": 3600,  # 1 hour
            "cleanup_interval": 1800   # 30 minutes
        }
    
    def create_connector(self, specification: ConnectorSpecification, 
                        credentials: Dict[str, str] = None) -> str:
        """Create a new connector instance"""
        connector_id = str(uuid.uuid4())
        
        if credentials is None:
            credentials = {}
        
        # Create connector instance
        connector = ConnectorInstance(
            id=connector_id,
            specification=specification,
            credentials=credentials,
            session_data={},
            last_used=datetime.now(),
            usage_count=0,
            success_rate=1.0,
            status="created"
        )
        
        self.connectors[connector_id] = connector
        
        # Initialize connector
        self._initialize_connector(connector)
        
        logger.info(f"Created connector {specification.name} with ID {connector_id}")
        return connector_id
    
    def _initialize_connector(self, connector: ConnectorInstance):
        """Initialize connector with authentication and setup"""
        try:
            # Handle authentication
            if connector.specification.authentication == AuthenticationType.OAUTH:
                self._setup_oauth_auth(connector)
            elif connector.specification.authentication == AuthenticationType.API_KEY:
                self._setup_api_key_auth(connector)
            elif connector.specification.authentication == AuthenticationType.BASIC:
                self._setup_basic_auth(connector)
            
            # Test connection
            self._test_connector(connector)
            
            connector.status = "active"
            logger.info(f"Connector {connector.id} initialized successfully")
            
        except Exception as e:
            connector.status = "error"
            logger.error(f"Connector initialization failed: {e}")
    
    def _setup_oauth_auth(self, connector: ConnectorInstance):
        """Setup OAuth authentication"""
        # This would implement OAuth flow
        # For now, simulate token storage
        if "access_token" in connector.credentials:
            self.auth_tokens[connector.id] = {
                "access_token": connector.credentials["access_token"],
                "refresh_token": connector.credentials.get("refresh_token", ""),
                "expires_at": datetime.now().timestamp() + 3600
            }
    
    def _setup_api_key_auth(self, connector: ConnectorInstance):
        """Setup API key authentication"""
        # Store API key securely
        if "api_key" in connector.credentials:
            self.auth_tokens[connector.id] = {
                "api_key": connector.credentials["api_key"],
                "added_at": datetime.now().isoformat()
            }
    
    def _setup_basic_auth(self, connector: ConnectorInstance):
        """Setup basic authentication"""
        if "username" in connector.credentials and "password" in connector.credentials:
            self.auth_tokens[connector.id] = {
                "username": connector.credentials["username"],
                "password": connector.credentials["password"],
                "auth_string": f"{connector.credentials['username']}:{connector.credentials['password']}"
            }
    
    def _test_connector(self, connector: ConnectorInstance):
        """Test connector functionality"""
        # Make a simple test request
        test_endpoint = list(connector.specification.endpoints.values())[0]
        
        try:
            response = self._make_request(connector, "GET", test_endpoint, {})
            if response.get("success"):
                logger.info(f"Connector {connector.id} test successful")
            else:
                logger.warning(f"Connector {connector.id} test failed: {response.get('error')}")
        except Exception as e:
            logger.error(f"Connector test error: {e}")
    
    def connect_to_system(self, system_type: str, credentials: Dict[str, str] = None) -> str:
        """Connect to any external system automatically"""
        
        # Determine connector type
        connector_type = self._determine_connector_type(system_type)
        
        # Find or create appropriate connector specification
        spec = self._find_or_create_spec(system_type, connector_type)
        
        # Create connector instance
        connector_id = self.create_connector(spec, credentials)
        
        return connector_id
    
    def _determine_connector_type(self, system_type: str) -> ConnectorType:
        """Determine connector type based on system type"""
        system_lower = system_type.lower()
        
        if any(word in system_lower for word in ["grant", "government", "federal", "state"]):
            return ConnectorType.GOVERNMENT
        elif any(word in system_lower for word in ["foundation", "nonprofit", "charity"]):
            return ConnectorType.FOUNDATION
        elif any(word in system_lower for word in ["community", "volunteer", "local"]):
            return ConnectorType.COMMUNITY
        elif any(word in system_lower for word in ["financial", "accounting", "budget", "quickbooks"]):
            return ConnectorType.FINANCIAL
        elif any(word in system_lower for word in ["document", "file", "storage", "drive"]):
            return ConnectorType.DOCUMENT
        elif any(word in system_lower for word in ["api", "rest", "webhook"]):
            return ConnectorType.API
        elif any(word in system_lower for word in ["database", "sql", "postgres", "mysql"]):
            return ConnectorType.DATABASE
        else:
            return ConnectorType.API  # Default
    
    def _find_or_create_spec(self, system_type: str, connector_type: ConnectorType) -> ConnectorSpecification:
        """Find existing spec or create new one for system"""
        
        # Check if we have a built-in spec for this system type
        for spec_name, spec in self.connector_specs.items():
            if system_type.lower() in spec_name.lower():
                return spec
        
        # Create new specification
        new_spec = ConnectorSpecification(
            name=f"{system_type}_connector",
            description=f"Auto-generated connector for {system_type}",
            connector_type=connector_type,
            base_url="https://api.example.com",  # Placeholder
            authentication=AuthenticationType.API_KEY,
            endpoints={
                "default": "/api",
                "data": "/data",
                "status": "/status"
            },
            parameters={
                "api_key": "string",
                "endpoint": "string"
            },
            rate_limits={
                "requests_per_minute": 60,
                "requests_per_hour": 1000
            },
            capabilities=["data_access", "status_check", "basic_operations"]
        )
        
        self.connector_specs[new_spec.name] = new_spec
        return new_spec
    
    def execute_operation(self, connector_id: str, operation: str, 
                         parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute operation on connected system"""
        
        if connector_id not in self.connectors:
            return {"success": False, "error": "Connector not found"}
        
        connector = self.connectors[connector_id]
        
        # Check rate limits
        if not self._check_rate_limit(connector_id, operation):
            return {"success": False, "error": "Rate limit exceeded"}
        
        try:
            # Find appropriate endpoint
            endpoint = connector.specification.endpoints.get(operation, f"/api/{operation}")
            
            # Make request
            response = self._make_request(connector, "GET", endpoint, parameters or {})
            
            # Update connector statistics
            connector.usage_count += 1
            connector.last_used = datetime.now()
            
            if response.get("success"):
                # Update success rate
                if connector.usage_count > 1:
                    connector.success_rate = ((connector.success_rate * (connector.usage_count - 1)) + 1) / connector.usage_count
            else:
                # Update failure rate
                if connector.usage_count > 1:
                    connector.success_rate = (connector.success_rate * (connector.usage_count - 1)) / connector.usage_count
            
            return response
            
        except Exception as e:
            logger.error(f"Operation execution error: {e}")
            return {"success": False, "error": str(e)}
    
    def _make_request(self, connector: ConnectorInstance, method: str, 
                     endpoint: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request through connector"""
        
        # Build URL
        url = urllib.parse.urljoin(connector.specification.base_url, endpoint)
        
        # Setup headers
        headers = {
            "User-Agent": "Shoghi-Universal-Connector/1.0",
            "Content-Type": "application/json"
        }
        
        # Add authentication
        if connector.specification.authentication == AuthenticationType.API_KEY:
            if connector.id in self.auth_tokens:
                headers["Authorization"] = f"Bearer {self.auth_tokens[connector.id].get('api_key', '')}"
        elif connector.specification.authentication == AuthenticationType.OAUTH:
            if connector.id in self.auth_tokens:
                headers["Authorization"] = f"Bearer {self.auth_tokens[connector.id].get('access_token', '')}"
        
        # Make request
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=parameters, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=parameters, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=parameters, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, params=parameters, timeout=30)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            # Process response
            if response.status_code < 400:
                try:
                    data = response.json()
                except:
                    data = response.text
                
                return {
                    "success": True,
                    "data": data,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {e}"}
    
    def _check_rate_limit(self, connector_id: str, operation: str) -> bool:
        """Check if operation is within rate limits"""
        
        current_time = time.time()
        
        if connector_id not in self.rate_limiter:
            self.rate_limiter[connector_id] = {}
        
        connector_limits = self.rate_limiter[connector_id]
        
        # Check minute limit
        minute_key = f"minute_{int(current_time / 60)}"
        if minute_key in connector_limits:
            if connector_limits[minute_key] >= 60:  # Default limit
                return False
        else:
            connector_limits[minute_key] = 0
        
        # Check hour limit
        hour_key = f"hour_{int(current_time / 3600)}"
        if hour_key in connector_limits:
            if connector_limits[hour_key] >= 1000:  # Default limit
                return False
        else:
            connector_limits[hour_key] = 0
        
        # Increment counters
        connector_limits[minute_key] += 1
        connector_limits[hour_key] += 1
        
        return True
    
    def discover_and_connect(self, target_system: str, 
                           auto_configure: bool = True) -> str:
        """Automatically discover and connect to a system"""
        
        logger.info(f"Discovering and connecting to: {target_system}")
        
        # Try common connection patterns
        connector_id = None
        
        # Try direct connection
        try:
            connector_id = self.connect_to_system(target_system)
            
            if auto_configure:
                # Auto-configure based on successful connection
                self._auto_configure_connector(connector_id, target_system)
            
            return connector_id
            
        except Exception as e:
            logger.error(f"Discovery and connection failed: {e}")
            return ""
    
    def _auto_configure_connector(self, connector_id: str, target_system: str):
        """Auto-configure connector based on system type"""
        # This would implement intelligent auto-configuration
        # For now, just log the attempt
        logger.info(f"Auto-configuring connector {connector_id} for {target_system}")
    
    def batch_execute(self, connector_id: str, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple operations in batch"""
        results = []
        
        for operation in operations:
            result = self.execute_operation(
                connector_id,
                operation["operation"],
                operation.get("parameters", {})
            )
            results.append(result)
        
        return results
    
    def get_connector_status(self, connector_id: str) -> Optional[Dict[str, Any]]:
        """Get connector status"""
        if connector_id not in self.connectors:
            return None
        
        connector = self.connectors[connector_id]
        
        return {
            "id": connector.id,
            "name": connector.specification.name,
            "type": connector.specification.connector_type.value,
            "status": connector.status,
            "usage_count": connector.usage_count,
            "success_rate": connector.success_rate,
            "last_used": connector.last_used.isoformat(),
            "capabilities": connector.specification.capabilities
        }
    
    def get_all_connectors_status(self) -> List[Dict[str, Any]]:
        """Get status of all connectors"""
        return [self.get_connector_status(connector_id) for connector_id in self.connectors]
    
    def search_grants_across_systems(self, search_terms: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search grants across multiple grant systems"""
        results = []
        
        # Find grant-related connectors
        grant_connectors = [
            conn for conn in self.connectors.values()
            if ConnectorType.GOVERNMENT in conn.specification.connector_type.value or
               ConnectorType.FOUNDATION in conn.specification.connector_type.value
        ]
        
        for connector in grant_connectors:
            try:
                # Search for grants
                search_result = self.execute_operation(
                    connector.id,
                    "search",
                    search_terms
                )
                
                if search_result.get("success"):
                    grants_data = search_result.get("data", [])
                    
                    # Add source information
                    if isinstance(grants_data, list):
                        for grant in grants_data:
                            grant["source_connector"] = connector.specification.name
                            grant["source_type"] = connector.specification.connector_type.value
                    
                    results.extend(grants_data if isinstance(grants_data, list) else [grants_data])
                
            except Exception as e:
                logger.error(f"Grant search failed for {connector.specification.name}: {e}")
        
        return results
    
    def sync_data_between_systems(self, source_connector_id: str, 
                                  target_connector_id: str,
                                  data_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Sync data between two connected systems"""
        
        try:
            # Get data from source
            source_data = self.execute_operation(source_connector_id, "data", {})
            
            if not source_data.get("success"):
                return {"success": False, "error": "Failed to get data from source"}
            
            # Transform data according to mapping
            transformed_data = self._transform_data(source_data["data"], data_mapping)
            
            # Send to target
            result = self.execute_operation(
                target_connector_id,
                "sync",
                {"data": transformed_data}
            )
            
            return {
                "success": result.get("success", False),
                "records_synced": len(transformed_data),
                "source_connector": source_connector_id,
                "target_connector": target_connector_id
            }
            
        except Exception as e:
            logger.error(f"Data sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _transform_data(self, data: Any, mapping: Dict[str, str]) -> Any:
        """Transform data according to mapping"""
        # This would implement data transformation logic
        # For now, return data as-is
        return data
    
    def get_connector_insights(self) -> Dict[str, Any]:
        """Get insights about connector usage and performance"""
        insights = {
            "total_connectors": len(self.connectors),
            "connectors_by_type": {},
            "most_used_connectors": [],
            "highest_success_rate": [],
            "recently_used": [],
            "system_coverage": {},
            "recommendations": []
        }
        
        # Count by type
        for connector in self.connectors.values():
            connector_type = connector.specification.connector_type.value
            insights["connectors_by_type"][connector_type] = insights["connectors_by_type"].get(connector_type, 0) + 1
        
        # Most used
        sorted_connectors = sorted(self.connectors.values(), key=lambda c: c.usage_count, reverse=True)
        insights["most_used_connectors"] = [
            {"name": c.specification.name, "usage_count": c.usage_count}
            for c in sorted_connectors[:5]
        ]
        
        # Highest success rate
        successful_connectors = sorted(self.connectors.values(), key=lambda c: c.success_rate, reverse=True)
        insights["highest_success_rate"] = [
            {"name": c.specification.name, "success_rate": c.success_rate}
            for c in successful_connectors[:5]
        ]
        
        # Recently used
        recent_connectors = sorted(self.connectors.values(), key=lambda c: c.last_used, reverse=True)
        insights["recently_used"] = [
            {"name": c.specification.name, "last_used": c.last_used.isoformat()}
            for c in recent_connectors[:5]
        ]
        
        # System coverage
        for connector in self.connectors.values():
            for capability in connector.specification.capabilities:
                insights["system_coverage"][capability] = insights["system_coverage"].get(capability, 0) + 1
        
        # Recommendations
        if len(self.connectors) < 5:
            insights["recommendations"].append({
                "type": "expansion",
                "message": "Consider adding more system connectors for broader coverage"
            })
        
        low_success_connectors = [c for c in self.connectors.values() if c.success_rate < 0.5]
        if len(low_success_connectors) > 0:
            insights["recommendations"].append({
                "type": "maintenance",
                "message": f"{len(low_success_connectors)} connectors have low success rates - check configurations"
            })
        
        return insights
    
    def cleanup_inactive_connectors(self, inactive_hours: int = 24):
        """Cleanup inactive connectors"""
        current_time = datetime.now()
        inactive_connectors = []
        
        for connector_id, connector in self.connectors.items():
            if (current_time - connector.last_used).total_seconds() > (inactive_hours * 3600):
                inactive_connectors.append(connector_id)
        
        for connector_id in inactive_connectors:
            del self.connectors[connector_id]
            # Clean up associated data
            if connector_id in self.auth_tokens:
                del self.auth_tokens[connector_id]
            if connector_id in self.rate_limiter:
                del self.rate_limiter[connector_id]
        
        logger.info(f"Cleaned up {len(inactive_connectors)} inactive connectors")
        return len(inactive_connectors)

# Global instance
universal_connector = UniversalConnector()

def connect_to_any_system(system_type: str, credentials: Dict[str, str] = None) -> str:
    """Connect to any external system"""
    return universal_connector.connect_to_system(system_type, credentials)