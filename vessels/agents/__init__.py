"""
Multi-class agent architecture with distinct moral geometries.

This module implements the agent class taxonomy where different agent types
have different constraint surfaces while maintaining universal truthfulness.

Key principles:
- ALL agents maintain high truthfulness (non-negotiable)
- Service/extraction ratios vary by class
- Radical transparency about agent class is mandatory
- Community servants control commercial agent access

Also includes specialized agents:
- Birth Agent: Conversational vessel creation
- MCP Explorer: Proactive capability discovery
- MCP Ambassador: Personified agents for MCP servers
"""

from .taxonomy import AgentClass, AgentRole
from .constraints import (
    ServantConstraints,
    CommercialAgentConstraints,
    HybridConsultantConstraints,
    get_constraints_for_class
)
from .disclosure import (
    CommercialAgentIntroduction,
    DisclosureProtocol
)
from .gateway import CommercialAgentGateway
from .mcp_ambassador import (
    MCPAmbassador,
    MCPAmbassadorPersona,
    MCPAmbassadorFactory,
    ambassador_factory,
)

__all__ = [
    # Agent taxonomy
    'AgentClass',
    'AgentRole',
    'ServantConstraints',
    'CommercialAgentConstraints',
    'HybridConsultantConstraints',
    'get_constraints_for_class',
    'CommercialAgentIntroduction',
    'DisclosureProtocol',
    'CommercialAgentGateway',
    # MCP Ambassadors
    'MCPAmbassador',
    'MCPAmbassadorPersona',
    'MCPAmbassadorFactory',
    'ambassador_factory',
]
