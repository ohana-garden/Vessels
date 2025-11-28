"""
Agent-to-Agent (A2A) Protocol Implementation for Vessels

Implements Google's A2A protocol for interoperable agent communication.
This enables vessels to discover, communicate with, and delegate tasks to other agents
both within Vessels and externally compliant systems.

Key concepts:
- Agent Card: JSON metadata describing a vessel's identity and capabilities
- Task: Stateful work item with lifecycle management
- Message: Communication unit between agents
- Discovery: Finding agents by capability, domain, or identity

A2A complements MCP:
- MCP provides tools and context (what an agent CAN do)
- A2A enables agent coordination (agents WORKING TOGETHER)

References:
- A2A Protocol: https://github.com/a2aproject/A2A
- NIP-01: Nostr protocol (used for transport)
"""

from .types import (
    # Core A2A types
    AgentCard,
    AgentSkill,
    Task,
    TaskState,
    Message,
    MessageRole,
    TextPart,
    FilePart,
    DataPart,
    # Authentication
    SecurityScheme,
    SecuritySchemeType,
)
from .service import (
    A2AService,
    A2AChannel,
)
from .discovery import (
    A2ADiscovery,
    AgentRegistry,
)

__all__ = [
    # Types
    'AgentCard',
    'AgentSkill',
    'Task',
    'TaskState',
    'Message',
    'MessageRole',
    'TextPart',
    'FilePart',
    'DataPart',
    'SecurityScheme',
    'SecuritySchemeType',
    # Service
    'A2AService',
    'A2AChannel',
    # Discovery
    'A2ADiscovery',
    'AgentRegistry',
]
