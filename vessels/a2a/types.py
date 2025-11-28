"""
A2A Protocol Types

Core type definitions implementing Google's A2A protocol specification.
These types enable interoperable agent-to-agent communication.

Protocol Version: 0.3.0 (as per A2A spec)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import uuid
import json


# =============================================================================
# Protocol Constants
# =============================================================================

A2A_PROTOCOL_VERSION = "0.3.0"


# =============================================================================
# Task Lifecycle States
# =============================================================================

class TaskState(str, Enum):
    """
    Task lifecycle states as defined in A2A protocol.

    States:
        PENDING: Task awaiting processing
        WORKING: Task currently being executed
        INPUT_REQUIRED: Task needs additional user input
        COMPLETED: Task finished successfully
        FAILED: Task encountered an error
        CANCELLED: Task cancelled by user
        REJECTED: Task rejected by server (won't process)
    """
    PENDING = "pending"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self in (TaskState.COMPLETED, TaskState.FAILED,
                       TaskState.CANCELLED, TaskState.REJECTED)


# =============================================================================
# Message Components
# =============================================================================

class MessageRole(str, Enum):
    """Role of message sender."""
    USER = "user"
    AGENT = "agent"


@dataclass
class TextPart:
    """Text content part."""
    text: str
    type: str = "text"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "text": self.text}


@dataclass
class FilePart:
    """File reference part."""
    file_uri: str
    media_type: str
    name: Optional[str] = None
    type: str = "file"

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "fileUri": self.file_uri,
            "mediaType": self.media_type,
        }
        if self.name:
            result["name"] = self.name
        return result


@dataclass
class DataPart:
    """Structured data part (JSON)."""
    data: Dict[str, Any]
    schema_uri: Optional[str] = None
    type: str = "data"

    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type, "data": self.data}
        if self.schema_uri:
            result["schemaUri"] = self.schema_uri
        return result


# Type alias for message parts
MessagePart = Union[TextPart, FilePart, DataPart]


@dataclass
class Message:
    """
    A2A message between agents.

    Messages contain parts (text, files, data) and track conversation context.
    """
    role: MessageRole
    parts: List[MessagePart]
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: Optional[str] = None
    context_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to A2A wire format (camelCase)."""
        result = {
            "role": self.role.value,
            "parts": [p.to_dict() for p in self.parts],
            "messageId": self.message_id,
        }
        if self.task_id:
            result["taskId"] = self.task_id
        if self.context_id:
            result["contextId"] = self.context_id
        return result

    @classmethod
    def from_text(cls, role: MessageRole, text: str, **kwargs) -> "Message":
        """Create a simple text message."""
        return cls(role=role, parts=[TextPart(text=text)], **kwargs)

    def get_text(self) -> str:
        """Extract text content from message parts."""
        texts = [p.text for p in self.parts if isinstance(p, TextPart)]
        return "\n".join(texts)


# =============================================================================
# Task Management
# =============================================================================

@dataclass
class TaskArtifact:
    """Artifact produced by a task."""
    artifact_id: str
    name: str
    description: Optional[str] = None
    parts: List[MessagePart] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifactId": self.artifact_id,
            "name": self.name,
            "description": self.description,
            "parts": [p.to_dict() for p in self.parts],
        }


@dataclass
class Task:
    """
    A2A Task - a stateful work item.

    Tasks track requests from one agent to another, maintaining
    state, messages, and artifacts throughout their lifecycle.
    """
    task_id: str
    context_id: str
    state: TaskState = TaskState.PENDING

    # Request from initiating agent
    request_message: Optional[Message] = None

    # Response from executing agent
    response_messages: List[Message] = field(default_factory=list)

    # Produced artifacts
    artifacts: List[TaskArtifact] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

    # Agent info
    requester_agent_id: Optional[str] = None
    executor_agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to A2A wire format."""
        result = {
            "taskId": self.task_id,
            "contextId": self.context_id,
            "state": self.state.value,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }
        if self.request_message:
            result["requestMessage"] = self.request_message.to_dict()
        if self.response_messages:
            result["responseMessages"] = [m.to_dict() for m in self.response_messages]
        if self.artifacts:
            result["artifacts"] = [a.to_dict() for a in self.artifacts]
        if self.error_message:
            result["errorMessage"] = self.error_message
        return result

    def transition_to(self, new_state: TaskState, error: Optional[str] = None) -> None:
        """Transition task to a new state."""
        self.state = new_state
        self.updated_at = datetime.utcnow()
        if error:
            self.error_message = error

    def add_response(self, message: Message) -> None:
        """Add a response message."""
        message.task_id = self.task_id
        message.context_id = self.context_id
        self.response_messages.append(message)
        self.updated_at = datetime.utcnow()

    @classmethod
    def create(
        cls,
        request_text: str,
        requester_id: str,
        executor_id: Optional[str] = None,
    ) -> "Task":
        """Create a new task from a text request."""
        task_id = str(uuid.uuid4())
        context_id = str(uuid.uuid4())

        return cls(
            task_id=task_id,
            context_id=context_id,
            request_message=Message.from_text(MessageRole.USER, request_text),
            requester_agent_id=requester_id,
            executor_agent_id=executor_id,
        )


# =============================================================================
# Agent Card - Identity & Capabilities
# =============================================================================

class SecuritySchemeType(str, Enum):
    """Authentication scheme types."""
    API_KEY = "apiKey"
    HTTP = "http"
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "openIdConnect"
    MUTUAL_TLS = "mutualTLS"


@dataclass
class SecurityScheme:
    """Authentication scheme for agent access."""
    scheme_type: SecuritySchemeType
    name: str
    description: Optional[str] = None
    # Additional fields depend on scheme type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.scheme_type.value,
            "name": self.name,
            "description": self.description,
        }


@dataclass
class AgentSkill:
    """
    Capability/skill advertised by an agent.

    Skills describe what an agent can do, helping other agents
    determine if this agent is suitable for a task.
    """
    skill_id: str
    name: str
    description: str
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    input_modes: List[str] = field(default_factory=lambda: ["text"])
    output_modes: List[str] = field(default_factory=lambda: ["text"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skillId": self.skill_id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "examples": self.examples,
            "inputModes": self.input_modes,
            "outputModes": self.output_modes,
        }


@dataclass
class AgentCard:
    """
    A2A Agent Card - JSON metadata describing an agent.

    Agent Cards are the foundation of A2A discovery and interaction.
    They describe who the agent is, what it can do, and how to communicate.

    In Vessels, each Vessel generates an Agent Card from its persona
    and capabilities, enabling interoperability with other A2A agents.
    """
    # Required fields
    name: str
    skills: List[AgentSkill]

    # Identity
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None

    # Endpoints
    url: Optional[str] = None  # Base URL for A2A operations

    # Provider info
    provider_name: Optional[str] = None
    provider_url: Optional[str] = None

    # Capabilities
    default_input_modes: List[str] = field(default_factory=lambda: ["text"])
    default_output_modes: List[str] = field(default_factory=lambda: ["text"])
    supports_streaming: bool = False
    supports_push_notifications: bool = False

    # Security
    security_schemes: List[SecurityScheme] = field(default_factory=list)

    # Protocol
    protocol_version: str = A2A_PROTOCOL_VERSION

    # Vessels-specific extensions
    vessel_id: Optional[str] = None
    project_id: Optional[str] = None
    domains: List[str] = field(default_factory=list)
    persona_style: Optional[str] = None
    nostr_pubkey: Optional[str] = None

    # Metadata
    icon_url: Optional[str] = None
    documentation_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to A2A wire format (camelCase per spec)."""
        result = {
            "protocolVersion": self.protocol_version,
            "name": self.name,
            "agentId": self.agent_id,
            "skills": [s.to_dict() for s in self.skills],
            "defaultInputModes": self.default_input_modes,
            "defaultOutputModes": self.default_output_modes,
            "capabilities": {
                "streaming": self.supports_streaming,
                "pushNotifications": self.supports_push_notifications,
            },
        }

        # Optional standard fields
        if self.description:
            result["description"] = self.description
        if self.url:
            result["url"] = self.url
        if self.provider_name:
            result["provider"] = {
                "name": self.provider_name,
                "url": self.provider_url,
            }
        if self.security_schemes:
            result["securitySchemes"] = [s.to_dict() for s in self.security_schemes]
        if self.icon_url:
            result["iconUrl"] = self.icon_url
        if self.documentation_url:
            result["documentationUrl"] = self.documentation_url

        # Vessels extensions (prefixed)
        if self.vessel_id:
            result["x-vessels-vesselId"] = self.vessel_id
        if self.project_id:
            result["x-vessels-projectId"] = self.project_id
        if self.domains:
            result["x-vessels-domains"] = self.domains
        if self.persona_style:
            result["x-vessels-personaStyle"] = self.persona_style
        if self.nostr_pubkey:
            result["x-vessels-nostrPubkey"] = self.nostr_pubkey

        return result

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCard":
        """Parse Agent Card from dictionary."""
        skills = [
            AgentSkill(
                skill_id=s.get("skillId", str(uuid.uuid4())),
                name=s["name"],
                description=s.get("description", ""),
                tags=s.get("tags", []),
                examples=s.get("examples", []),
                input_modes=s.get("inputModes", ["text"]),
                output_modes=s.get("outputModes", ["text"]),
            )
            for s in data.get("skills", [])
        ]

        return cls(
            name=data["name"],
            skills=skills,
            agent_id=data.get("agentId", str(uuid.uuid4())),
            description=data.get("description"),
            url=data.get("url"),
            protocol_version=data.get("protocolVersion", A2A_PROTOCOL_VERSION),
            default_input_modes=data.get("defaultInputModes", ["text"]),
            default_output_modes=data.get("defaultOutputModes", ["text"]),
            supports_streaming=data.get("capabilities", {}).get("streaming", False),
            supports_push_notifications=data.get("capabilities", {}).get("pushNotifications", False),
            vessel_id=data.get("x-vessels-vesselId"),
            project_id=data.get("x-vessels-projectId"),
            domains=data.get("x-vessels-domains", []),
            persona_style=data.get("x-vessels-personaStyle"),
            nostr_pubkey=data.get("x-vessels-nostrPubkey"),
        )

    def matches_need(self, need_description: str, required_tags: Optional[List[str]] = None) -> float:
        """
        Score how well this agent matches a need.

        Returns a score from 0.0 to 1.0.
        """
        score = 0.0
        need_lower = need_description.lower()

        # Check skill descriptions
        for skill in self.skills:
            if any(word in skill.description.lower() for word in need_lower.split()):
                score += 0.3
            if any(word in skill.name.lower() for word in need_lower.split()):
                score += 0.2
            # Check tags
            if required_tags:
                matching_tags = set(skill.tags) & set(required_tags)
                score += 0.1 * len(matching_tags)

        # Check domains
        for domain in self.domains:
            if domain.lower() in need_lower:
                score += 0.2

        return min(score, 1.0)
