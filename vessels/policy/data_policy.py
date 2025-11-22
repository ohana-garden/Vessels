"""
Data governance policy definitions.

Defines allowed node types and relationship types per privacy level,
and provides policy lookup functions.
"""

from typing import List, Dict, Set
from vessels.knowledge.schema import NodeType, RelationType, CommunityPrivacy


# Node types allowed per privacy level for cross-community queries
PRIVACY_NODE_POLICIES: Dict[CommunityPrivacy, Set[NodeType]] = {
    CommunityPrivacy.PRIVATE: set(),  # No cross-community access
    CommunityPrivacy.SHARED: {
        # Shared: read-only for non-sensitive nodes
        NodeType.PLACE,
        NodeType.ORGANIZATION,
        NodeType.RESOURCE,
        NodeType.EVENT,
    },
    CommunityPrivacy.PUBLIC: {
        # Public: broader access but still filtered
        NodeType.PLACE,
        NodeType.ORGANIZATION,
        NodeType.RESOURCE,
        NodeType.EVENT,
        NodeType.FACT,  # General facts OK
        NodeType.PATTERN,  # Patterns OK
    },
    CommunityPrivacy.FEDERATED: {
        # Federated: most types except sensitive personal data
        NodeType.PLACE,
        NodeType.ORGANIZATION,
        NodeType.RESOURCE,
        NodeType.EVENT,
        NodeType.SERVANT,
        NodeType.FACT,
        NodeType.PATTERN,
        NodeType.AGENT_STATE,
    },
}

# Relationship types allowed per privacy level
PRIVACY_RELATIONSHIP_POLICIES: Dict[CommunityPrivacy, Set[RelationType]] = {
    CommunityPrivacy.PRIVATE: set(),  # No cross-community access
    CommunityPrivacy.SHARED: {
        RelationType.LOCATED_AT,
        RelationType.HAS_RESOURCE,
        RelationType.PARTICIPATES_IN,
    },
    CommunityPrivacy.PUBLIC: {
        RelationType.LOCATED_AT,
        RelationType.HAS_RESOURCE,
        RelationType.PARTICIPATES_IN,
        RelationType.PROVIDES,
        RelationType.RELATES_TO,
    },
    CommunityPrivacy.FEDERATED: {
        RelationType.LOCATED_AT,
        RelationType.HAS_RESOURCE,
        RelationType.PARTICIPATES_IN,
        RelationType.PROVIDES,
        RelationType.SERVES,
        RelationType.COORDINATES_WITH,
        RelationType.HAS_STATE,
        RelationType.REMEMBERS,
        RelationType.RELATES_TO,
        RelationType.SPAWNED_BY,
    },
}


def get_allowed_node_types(privacy_level: CommunityPrivacy) -> Set[NodeType]:
    """
    Get allowed node types for a privacy level.

    Args:
        privacy_level: Privacy level

    Returns:
        Set of allowed NodeTypes
    """
    return PRIVACY_NODE_POLICIES.get(privacy_level, set())


def get_allowed_relationship_types(privacy_level: CommunityPrivacy) -> Set[RelationType]:
    """
    Get allowed relationship types for a privacy level.

    Args:
        privacy_level: Privacy level

    Returns:
        Set of allowed RelationTypes
    """
    return PRIVACY_RELATIONSHIP_POLICIES.get(privacy_level, set())


def is_node_type_allowed(
    privacy_level: CommunityPrivacy,
    node_type: NodeType
) -> bool:
    """
    Check if a node type is allowed for cross-community access.

    Args:
        privacy_level: Privacy level of the source vessel
        node_type: Node type to check

    Returns:
        True if allowed, False otherwise
    """
    allowed = get_allowed_node_types(privacy_level)
    return node_type in allowed


def is_relationship_type_allowed(
    privacy_level: CommunityPrivacy,
    relationship_type: RelationType
) -> bool:
    """
    Check if a relationship type is allowed for cross-community access.

    Args:
        privacy_level: Privacy level of the source vessel
        relationship_type: Relationship type to check

    Returns:
        True if allowed, False otherwise
    """
    allowed = get_allowed_relationship_types(privacy_level)
    return relationship_type in allowed


# Per-vessel overrides (can be extended with configuration)
VESSEL_POLICY_OVERRIDES: Dict[str, Dict[str, Set]] = {}


def get_vessel_allowed_nodes(
    vessel_id: str,
    default_privacy: CommunityPrivacy
) -> Set[NodeType]:
    """
    Get allowed node types for a specific vessel.

    Checks for vessel-specific overrides, falls back to privacy level default.

    Args:
        vessel_id: Vessel ID
        default_privacy: Default privacy level

    Returns:
        Set of allowed NodeTypes
    """
    if vessel_id in VESSEL_POLICY_OVERRIDES:
        return VESSEL_POLICY_OVERRIDES[vessel_id].get("nodes", get_allowed_node_types(default_privacy))
    return get_allowed_node_types(default_privacy)


def set_vessel_policy_override(
    vessel_id: str,
    allowed_nodes: Set[NodeType],
    allowed_relationships: Set[RelationType]
) -> None:
    """
    Set vessel-specific policy overrides.

    Args:
        vessel_id: Vessel ID
        allowed_nodes: Allowed node types
        allowed_relationships: Allowed relationship types
    """
    VESSEL_POLICY_OVERRIDES[vessel_id] = {
        "nodes": allowed_nodes,
        "relationships": allowed_relationships
    }
