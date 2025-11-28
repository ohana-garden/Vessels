"""
Vessels Knowledge Graph Schema

Defines the node types, relationship types, and properties for the
Vessels temporal knowledge graph backed by FalkorDB.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class NodeType(str, Enum):
    """Node types in the Vessels knowledge graph"""
    PERSON = "Person"              # Kupuna, caregivers, volunteers
    PLACE = "Place"                # Gardens, medical facilities, homes
    ORGANIZATION = "Organization"  # Health providers, food hubs
    EVENT = "Event"                # Appointments, deliveries, gatherings
    SERVANT = "Servant"            # AI servants
    RESOURCE = "Resource"          # Vans, food, supplies
    EXPERIENCE = "Experience"      # Memory: what was tried
    FACT = "Fact"                  # Memory: factual information
    PATTERN = "Pattern"            # Memory: recurring situations
    CONTRIBUTION = "Contribution"  # Kala-valued contributions
    AGENT_STATE = "AgentState"     # 12D phase space state
    COMMERCIAL_AGENT = "CommercialAgent"  # Commercial agents with fee structures
    COMMERCIAL_TRANSACTION = "CommercialTransaction"  # Referral fee transactions
    FUND_ALLOCATION = "FundAllocation"  # Community fund allocations

    # Tools and Capabilities (A0 tool registry)
    TOOL = "Tool"                  # Capability that agents can use
    MCP_SERVER = "MCPServer"       # MCP server providing tools
    CAPABILITY = "Capability"      # High-level capability (weather, scheduling, etc.)

    # Vessels core
    PROJECT = "Project"            # Bounded collaborative space (community)
    VESSEL = "Vessel"              # Personified digital twin


class RelationType(str, Enum):
    """Relationship types in the Vessels knowledge graph"""
    NEEDS = "NEEDS"                      # Person -[NEEDS]-> Service/Resource
    PROVIDES = "PROVIDES"                # Person/Org -[PROVIDES]-> Service/Resource
    SERVES = "SERVES"                    # Servant -[SERVES]-> Person
    COORDINATES_WITH = "COORDINATES_WITH"  # Servant -[COORDINATES_WITH]-> Servant
    LOCATED_AT = "LOCATED_AT"           # Event/Person -[LOCATED_AT]-> Place
    HAS_RESOURCE = "HAS_RESOURCE"       # Org -[HAS_RESOURCE]-> Resource
    PARTICIPATES_IN = "PARTICIPATES_IN"  # Person -[PARTICIPATES_IN]-> Event
    HAS_STATE = "HAS_STATE"             # Servant -[HAS_STATE]-> AgentState
    REMEMBERS = "REMEMBERS"             # Servant -[REMEMBERS]-> Experience/Fact/Pattern
    RELATES_TO = "RELATES_TO"           # Memory -[RELATES_TO]-> Memory
    CONTRIBUTED_BY = "CONTRIBUTED_BY"   # Contribution -[CONTRIBUTED_BY]-> Person
    SPAWNED_BY = "SPAWNED_BY"           # Servant -[SPAWNED_BY]-> Servant
    REPRESENTS = "REPRESENTS"           # CommercialAgent -[REPRESENTS]-> Organization
    PAID_BY = "PAID_BY"                 # Transaction -[PAID_BY]-> Organization
    PAID_TO = "PAID_TO"                 # Transaction -[PAID_TO]-> FundAllocation
    ALLOCATED_FOR = "ALLOCATED_FOR"     # FundAllocation -[ALLOCATED_FOR]-> Category

    # Tool relationships
    PROVIDES_TOOL = "PROVIDES_TOOL"     # MCPServer -[PROVIDES_TOOL]-> Tool
    HAS_CAPABILITY = "HAS_CAPABILITY"   # Tool -[HAS_CAPABILITY]-> Capability
    SOLVES_PROBLEM = "SOLVES_PROBLEM"   # Tool -[SOLVES_PROBLEM]-> description
    USES_TOOL = "USES_TOOL"             # Agent/Vessel -[USES_TOOL]-> Tool
    CONNECTED_TO = "CONNECTED_TO"       # Vessel -[CONNECTED_TO]-> MCPServer
    RECOMMENDED_FOR = "RECOMMENDED_FOR" # Tool -[RECOMMENDED_FOR]-> vessel_type

    # Vessel relationships
    HOSTS = "HOSTS"                     # Project -[HOSTS]-> Vessel
    MEMBER_OF = "MEMBER_OF"             # Person -[MEMBER_OF]-> Project
    OWNS = "OWNS"                       # Person -[OWNS]-> Project


class PropertyName(str, Enum):
    """Common property names across nodes"""
    COMMUNITY_ID = "community_id"
    VALID_AT = "valid_at"          # Temporal validity start
    INVALID_AT = "invalid_at"      # Temporal validity end
    CREATED_BY = "created_by"      # Servant ID that created this
    CREATED_AT = "created_at"      # Creation timestamp
    NAME = "name"
    TYPE = "type"
    STATUS = "status"
    DESCRIPTION = "description"


class VesselsGraphSchema:
    """
    Comprehensive schema for Vessels knowledge graph

    This schema supports:
    - Community memory and relationships
    - Servant coordination and spawning
    - 12D phase space state tracking
    - Temporal validity for all facts
    - Cross-community coordination with privacy
    """

    # Node type definitions with their required properties
    NODE_SCHEMAS: Dict[NodeType, List[str]] = {
        NodeType.PERSON: [
            PropertyName.NAME,
            PropertyName.COMMUNITY_ID,
            PropertyName.VALID_AT,
        ],
        NodeType.PLACE: [
            PropertyName.NAME,
            PropertyName.TYPE,
            PropertyName.COMMUNITY_ID,
        ],
        NodeType.ORGANIZATION: [
            PropertyName.NAME,
            PropertyName.TYPE,
            PropertyName.COMMUNITY_ID,
        ],
        NodeType.EVENT: [
            PropertyName.NAME,
            PropertyName.TYPE,
            PropertyName.VALID_AT,
            PropertyName.COMMUNITY_ID,
        ],
        NodeType.SERVANT: [
            PropertyName.NAME,
            PropertyName.TYPE,
            PropertyName.STATUS,
            PropertyName.COMMUNITY_ID,
            PropertyName.CREATED_AT,
        ],
        NodeType.RESOURCE: [
            PropertyName.NAME,
            PropertyName.TYPE,
            PropertyName.COMMUNITY_ID,
        ],
        NodeType.AGENT_STATE: [
            PropertyName.CREATED_AT,
            PropertyName.COMMUNITY_ID,
            "activity",
            "coordination",
            "effectiveness",
            "resource_consumption",
            "system_health",
            "truthfulness",
            "justice",
            "trustworthiness",
            "unity",
            "service",
            "detachment",
            "understanding",
        ],
        # Tool registry
        NodeType.TOOL: [
            PropertyName.NAME,
            PropertyName.DESCRIPTION,
            "tool_id",
            "capabilities",          # List of high-level capabilities
            "problems_it_solves",    # Natural language problems
            "parameters_schema",     # JSON schema for tool parameters
            "provider_type",         # "mcp", "native", "custom"
            "provider_id",           # MCP server ID or "native"
            "trust_level",           # "verified", "community", "unknown"
            "cost_model",            # "free", "free_tier", "per_call", "subscription"
            "recommended_for",       # List of vessel types
            "domains",               # List of domains (agriculture, scheduling, etc.)
        ],
        NodeType.MCP_SERVER: [
            PropertyName.NAME,
            PropertyName.DESCRIPTION,
            "server_id",
            "endpoint",              # npx command or URL
            "auth_required",
            "auth_type",             # "api_key", "oauth", None
            "trust_level",
            "status",                # "online", "offline", "degraded"
            "reliability_score",     # 0-1 based on history
            "cost_model",
            "source",                # "npm", "github", "community", "manual"
            "discovered_at",
        ],
        NodeType.CAPABILITY: [
            PropertyName.NAME,
            PropertyName.DESCRIPTION,
            "capability_id",
            "category",              # "communication", "data", "scheduling", etc.
            "keywords",              # Search keywords
        ],
        # Vessels core entities
        NodeType.PROJECT: [
            PropertyName.NAME,
            PropertyName.DESCRIPTION,
            "project_id",
            "owner_id",
            "graph_namespace",
            "privacy_level",
            "governance",
            PropertyName.STATUS,
            PropertyName.CREATED_AT,
        ],
        NodeType.VESSEL: [
            PropertyName.NAME,
            PropertyName.DESCRIPTION,
            "vessel_id",
            "project_id",
            "graph_namespace",
            "privacy_level",
            "persona",               # JSON persona configuration
            PropertyName.STATUS,
            PropertyName.CREATED_AT,
        ],
    }

    @staticmethod
    def get_required_properties(node_type: NodeType) -> List[str]:
        """Get required properties for a node type"""
        return VesselsGraphSchema.NODE_SCHEMAS.get(node_type, [])

    @staticmethod
    def validate_node_properties(node_type: NodeType, properties: Dict[str, Any]) -> bool:
        """Validate that a node has all required properties"""
        required = VesselsGraphSchema.get_required_properties(node_type)
        return all(prop in properties for prop in required)

    @staticmethod
    def create_community_graph_name(community_id: str) -> str:
        """Generate graph name for a community"""
        return f"{community_id}_graph"

    @staticmethod
    def is_temporal_node(node_type: NodeType) -> bool:
        """Check if node type supports temporal validity"""
        return node_type in [
            NodeType.PERSON,
            NodeType.EVENT,
            NodeType.AGENT_STATE,
            NodeType.EXPERIENCE,
            NodeType.FACT,
        ]


# Predefined servant types for Project templates
class ServantType(str, Enum):
    """Types of servants that can be spawned"""
    TRANSPORT = "transport"
    MEALS = "meals"
    MEDICAL = "medical"
    GARDEN = "garden"
    GRANT_WRITER = "grant_writer"
    VOLUNTEER_COORDINATOR = "volunteer_coordinator"
    VOICE_INTERFACE = "voice_interface"
    COMMUNITY_COORDINATOR = "community_coordinator"
    COMMERCIAL = "commercial"  # Commercial agents with fee structures


# Privacy levels for cross-community access
class CommunityPrivacy(str, Enum):
    """Privacy levels for community graphs"""
    PRIVATE = "private"        # No cross-community reads
    SHARED = "shared"          # Read-only to trusted communities
    PUBLIC = "public"          # Read-only to all servants
    FEDERATED = "federated"    # Read/write coordination space


# Tool trust levels
class ToolTrustLevel(str, Enum):
    """Trust levels for tools and MCP servers"""
    VERIFIED = "verified"      # Officially verified, high trust
    COMMUNITY = "community"    # Community-vetted, moderate trust
    UNKNOWN = "unknown"        # Not yet evaluated
    UNTRUSTED = "untrusted"    # Known issues or suspicious


# Tool cost models
class ToolCostModel(str, Enum):
    """Cost models for tool usage"""
    FREE = "free"              # Always free
    FREE_TIER = "free_tier"    # Free up to limits
    PER_CALL = "per_call"      # Pay per use
    SUBSCRIPTION = "subscription"  # Requires subscription
    UNKNOWN = "unknown"        # Cost not determined


# Tool provider types
class ToolProviderType(str, Enum):
    """How a tool is provided/accessed"""
    NATIVE = "native"          # Built into A0/Claude
    MCP = "mcp"                # Via MCP server
    CUSTOM = "custom"          # Custom implementation
    VESSEL = "vessel"          # Provided by another vessel


# Capability categories
class CapabilityCategory(str, Enum):
    """High-level capability categories"""
    COMMUNICATION = "communication"  # Email, SMS, messaging
    SCHEDULING = "scheduling"        # Calendar, reminders, timing
    DATA = "data"                    # Weather, maps, research
    STORAGE = "storage"              # Files, memory
    INTEGRATION = "integration"      # External services
    COORDINATION = "coordination"    # Multi-agent coordination
    KNOWLEDGE = "knowledge"          # Search, lookup, learning
