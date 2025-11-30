"""
Serverless Smart Function (SSF) Schema Definitions.

SSFs are stateless, atomic, ethically-bound execution units.
They are the ONLY way A0 agents can affect the external world.

This module defines the core data structures for SSF definitions,
constraint binding configuration, and execution results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4


class SSFCategory(str, Enum):
    """
    Categories that map to permission domains.

    SSF categories determine which constraints apply during validation
    and help with SSF discovery based on capability needs.
    """
    COMMUNICATION = "communication"      # SMS, email, notifications
    DATA_RETRIEVAL = "data_retrieval"    # Read-only data access
    DATA_MUTATION = "data_mutation"      # Write operations
    SCHEDULING = "scheduling"            # Calendar, appointments
    COMPUTATION = "computation"          # Pure calculations
    EXTERNAL_API = "external_api"        # Third-party service calls
    AGENT_COORDINATION = "agent_coordination"  # A2A, delegation
    FILE_OPERATIONS = "file_operations"  # File system access
    MEMORY_OPERATIONS = "memory_operations"  # Graphiti/shared memory


class RiskLevel(str, Enum):
    """
    Risk classification for SSFs.

    Risk level affects:
    - Required approval thresholds
    - Constraint binding strictness
    - Logging verbosity
    - Escalation triggers
    """
    LOW = "low"          # Read-only, no side effects
    MEDIUM = "medium"    # Reversible side effects
    HIGH = "high"        # Irreversible side effects (sending messages, etc.)
    CRITICAL = "critical"  # Financial, health, or safety implications


class HandlerType(str, Enum):
    """Types of SSF execution handlers."""
    INLINE = "inline"        # Python code as string (for simple, auditable SSFs)
    MODULE = "module"        # Reference to Python module
    CONTAINER = "container"  # Docker image reference
    MCP = "mcp"              # MCP tool wrapper
    REMOTE = "remote"        # HTTP endpoint


class ConstraintBindingMode(str, Enum):
    """
    How ethical constraints propagate to SSF execution.

    This determines the scope of constraint inheritance from the
    invoking persona's manifold position.
    """
    FULL = "full"        # SSF inherits complete manifold position
    FILTERED = "filtered"  # Only constraints relevant to SSF's category
    EXPLICIT = "explicit"  # Only constraints listed explicitly


class BoundaryBehavior(str, Enum):
    """
    How to handle operations approaching constraint boundaries.
    """
    BLOCK = "block"        # Reject operations near boundaries
    ESCALATE = "escalate"  # Request supervisor approval
    WARN = "warn"          # Allow with warning logged


class SSFStatus(str, Enum):
    """SSF execution status."""
    SUCCESS = "success"
    BLOCKED = "blocked"
    ESCALATED = "escalated"
    TIMEOUT = "timeout"
    ERROR = "error"
    OUTPUT_BLOCKED = "output_blocked"
    PARTIAL = "partial"  # For compositions


@dataclass
class SSFHandler:
    """
    Specifies how an SSF executes.

    Each SSF has exactly one handler type that determines how
    it processes inputs and produces outputs.
    """
    type: HandlerType

    # For inline: Python code as string (for simple, auditable SSFs)
    inline_code: Optional[str] = None

    # For module: Reference to Python module
    module_path: Optional[str] = None  # e.g., "vessels.ssf.builtins.send_sms"
    function_name: Optional[str] = None

    # For container: Docker image reference
    container_image: Optional[str] = None
    container_command: Optional[List[str]] = None

    # For MCP: Tool reference
    mcp_server: Optional[str] = None
    mcp_tool: Optional[str] = None

    # For remote: HTTP endpoint
    remote_url: Optional[str] = None
    remote_method: str = "POST"
    remote_headers: Optional[Dict[str, str]] = None

    # Cached callable for module handlers
    _implementation: Optional[Callable] = field(default=None, repr=False, compare=False)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": self.type.value,
            "inline_code": self.inline_code,
            "module_path": self.module_path,
            "function_name": self.function_name,
            "container_image": self.container_image,
            "container_command": self.container_command,
            "mcp_server": self.mcp_server,
            "mcp_tool": self.mcp_tool,
            "remote_url": self.remote_url,
            "remote_method": self.remote_method,
            "remote_headers": self.remote_headers,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SSFHandler":
        """Create from dictionary."""
        return cls(
            type=HandlerType(d["type"]),
            inline_code=d.get("inline_code"),
            module_path=d.get("module_path"),
            function_name=d.get("function_name"),
            container_image=d.get("container_image"),
            container_command=d.get("container_command"),
            mcp_server=d.get("mcp_server"),
            mcp_tool=d.get("mcp_tool"),
            remote_url=d.get("remote_url"),
            remote_method=d.get("remote_method", "POST"),
            remote_headers=d.get("remote_headers"),
        )

    @classmethod
    def inline(cls, code: str) -> "SSFHandler":
        """Create an inline handler."""
        return cls(type=HandlerType.INLINE, inline_code=code)

    @classmethod
    def module(cls, module_path: str, function_name: str) -> "SSFHandler":
        """Create a module handler."""
        return cls(
            type=HandlerType.MODULE,
            module_path=module_path,
            function_name=function_name,
        )

    @classmethod
    def mcp(cls, server: str, tool: str) -> "SSFHandler":
        """Create an MCP handler."""
        return cls(type=HandlerType.MCP, mcp_server=server, mcp_tool=tool)

    @classmethod
    def remote(
        cls,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None
    ) -> "SSFHandler":
        """Create a remote HTTP handler."""
        return cls(
            type=HandlerType.REMOTE,
            remote_url=url,
            remote_method=method,
            remote_headers=headers,
        )


@dataclass
class ConstraintBindingConfig:
    """
    Configures how ethical constraints propagate to SSF execution.

    This is the core safety mechanism - SSFs cannot escape the
    moral topology of their invoking persona.
    """
    mode: ConstraintBindingMode = ConstraintBindingMode.FULL

    # For explicit mode: list of constraint names to apply
    explicit_constraints: Optional[List[str]] = None

    # Validation configuration
    validate_inputs: bool = True   # Check inputs against manifold
    validate_outputs: bool = True  # Check outputs against manifold

    # Boundary behavior
    on_boundary_approach: BoundaryBehavior = BoundaryBehavior.BLOCK
    escalation_target: Optional[str] = None  # Persona role to escalate to

    # Forbidden patterns (hard-coded safety rails)
    forbidden_input_patterns: List[str] = field(default_factory=list)  # Regex patterns
    forbidden_output_patterns: List[str] = field(default_factory=list)

    # Boundary threshold (0-1, how close to constraint boundary triggers behavior)
    boundary_threshold: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "mode": self.mode.value,
            "explicit_constraints": self.explicit_constraints,
            "validate_inputs": self.validate_inputs,
            "validate_outputs": self.validate_outputs,
            "on_boundary_approach": self.on_boundary_approach.value,
            "escalation_target": self.escalation_target,
            "forbidden_input_patterns": self.forbidden_input_patterns,
            "forbidden_output_patterns": self.forbidden_output_patterns,
            "boundary_threshold": self.boundary_threshold,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ConstraintBindingConfig":
        """Create from dictionary."""
        return cls(
            mode=ConstraintBindingMode(d.get("mode", "full")),
            explicit_constraints=d.get("explicit_constraints"),
            validate_inputs=d.get("validate_inputs", True),
            validate_outputs=d.get("validate_outputs", True),
            on_boundary_approach=BoundaryBehavior(d.get("on_boundary_approach", "block")),
            escalation_target=d.get("escalation_target"),
            forbidden_input_patterns=d.get("forbidden_input_patterns", []),
            forbidden_output_patterns=d.get("forbidden_output_patterns", []),
            boundary_threshold=d.get("boundary_threshold", 0.1),
        )

    @classmethod
    def strict(cls) -> "ConstraintBindingConfig":
        """Create a strict configuration for high-risk SSFs."""
        return cls(
            mode=ConstraintBindingMode.FULL,
            validate_inputs=True,
            validate_outputs=True,
            on_boundary_approach=BoundaryBehavior.BLOCK,
            boundary_threshold=0.15,
        )

    @classmethod
    def permissive(cls) -> "ConstraintBindingConfig":
        """Create a permissive configuration for low-risk SSFs."""
        return cls(
            mode=ConstraintBindingMode.FILTERED,
            validate_inputs=True,
            validate_outputs=False,
            on_boundary_approach=BoundaryBehavior.WARN,
            boundary_threshold=0.05,
        )


@dataclass
class SSFDefinition:
    """
    Serverless Smart Function definition.

    SSFs are stateless, atomic, and ethically-bound execution units.
    They are the ONLY way A0 agents can affect the external world.
    """
    # Identity
    id: UUID = field(default_factory=uuid4)
    name: str = ""  # Unique identifier: "send_sms", "query_database"
    version: str = "1.0.0"  # Semantic versioning for SSF evolution

    # Categorization for permission matching
    category: SSFCategory = SSFCategory.COMPUTATION
    tags: List[str] = field(default_factory=list)  # Fine-grained categorization

    # Human-readable description
    description: str = ""
    description_for_llm: str = ""  # Optimized for LLM tool selection

    # Execution specification
    handler: Optional[SSFHandler] = None

    # I/O contracts (JSON Schema)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)

    # Resource requirements
    timeout_seconds: int = 30  # 1-900 seconds
    memory_mb: int = 128  # 64-3008 MB

    # Dependencies
    required_tools: List[str] = field(default_factory=list)  # MCP tools this SSF needs
    required_permissions: List[str] = field(default_factory=list)  # Persona permissions

    # Safety metadata
    risk_level: RiskLevel = RiskLevel.LOW
    side_effects: List[str] = field(default_factory=list)  # What external state this can modify
    reversible: bool = True  # Can effects be undone?

    # Constraint binding configuration
    constraint_binding: ConstraintBindingConfig = field(default_factory=ConstraintBindingConfig)

    # Provenance
    spawned_by: Optional[UUID] = None  # Persona ID that spawned this (if dynamic)
    spawned_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate and set defaults after initialization."""
        if self.timeout_seconds < 1:
            self.timeout_seconds = 1
        elif self.timeout_seconds > 900:
            self.timeout_seconds = 900

        if self.memory_mb < 64:
            self.memory_mb = 64
        elif self.memory_mb > 3008:
            self.memory_mb = 3008

        # Ensure id is UUID
        if isinstance(self.id, str):
            self.id = UUID(self.id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage."""
        return {
            "id": str(self.id),
            "name": self.name,
            "version": self.version,
            "category": self.category.value,
            "tags": self.tags,
            "description": self.description,
            "description_for_llm": self.description_for_llm,
            "handler": self.handler.to_dict() if self.handler else None,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "timeout_seconds": self.timeout_seconds,
            "memory_mb": self.memory_mb,
            "required_tools": self.required_tools,
            "required_permissions": self.required_permissions,
            "risk_level": self.risk_level.value,
            "side_effects": self.side_effects,
            "reversible": self.reversible,
            "constraint_binding": self.constraint_binding.to_dict(),
            "spawned_by": str(self.spawned_by) if self.spawned_by else None,
            "spawned_at": self.spawned_at.isoformat() if self.spawned_at else None,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SSFDefinition":
        """Create from dictionary."""
        return cls(
            id=UUID(d["id"]) if isinstance(d.get("id"), str) else d.get("id", uuid4()),
            name=d.get("name", ""),
            version=d.get("version", "1.0.0"),
            category=SSFCategory(d.get("category", "computation")),
            tags=d.get("tags", []),
            description=d.get("description", ""),
            description_for_llm=d.get("description_for_llm", ""),
            handler=SSFHandler.from_dict(d["handler"]) if d.get("handler") else None,
            input_schema=d.get("input_schema", {}),
            output_schema=d.get("output_schema", {}),
            timeout_seconds=d.get("timeout_seconds", 30),
            memory_mb=d.get("memory_mb", 128),
            required_tools=d.get("required_tools", []),
            required_permissions=d.get("required_permissions", []),
            risk_level=RiskLevel(d.get("risk_level", "low")),
            side_effects=d.get("side_effects", []),
            reversible=d.get("reversible", True),
            constraint_binding=ConstraintBindingConfig.from_dict(
                d.get("constraint_binding", {})
            ),
            spawned_by=UUID(d["spawned_by"]) if d.get("spawned_by") else None,
            spawned_at=datetime.fromisoformat(d["spawned_at"]) if d.get("spawned_at") else None,
            created_at=datetime.fromisoformat(d["created_at"]) if d.get("created_at") else datetime.utcnow(),
        )

    def matches_need(self, need: str) -> float:
        """Score how well this SSF matches a capability need (0-1)."""
        need_lower = need.lower()
        score = 0.0

        # Check name
        if need_lower in self.name.lower():
            score += 0.3

        # Check description
        if need_lower in self.description.lower():
            score += 0.2

        # Check tags
        for tag in self.tags:
            if tag.lower() in need_lower or need_lower in tag.lower():
                score += 0.15

        # Check category
        if self.category.value.replace("_", " ") in need_lower:
            score += 0.2

        # Check LLM description
        if self.description_for_llm and need_lower in self.description_for_llm.lower():
            score += 0.15

        return min(score, 1.0)


@dataclass
class ManifoldValidation:
    """Result of validating data against the ethical manifold."""
    blocked: bool = False
    violation: Optional[str] = None
    violations: List[str] = field(default_factory=list)
    boundary_warning: Optional[str] = None
    boundary_warnings: List[str] = field(default_factory=list)
    checked_constraints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "blocked": self.blocked,
            "violation": self.violation,
            "violations": self.violations,
            "boundary_warning": self.boundary_warning,
            "boundary_warnings": self.boundary_warnings,
            "checked_constraints": self.checked_constraints,
        }


@dataclass
class SSFResult:
    """Result of SSF execution."""
    status: SSFStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    constraint_violation: Optional[ManifoldValidation] = None
    escalation_reason: Optional[str] = None
    escalation_target: Optional[str] = None

    # Execution context
    ssf_id: Optional[UUID] = None
    ssf_name: Optional[str] = None
    invoked_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "execution_time_seconds": self.execution_time_seconds,
            "constraint_violation": self.constraint_violation.to_dict() if self.constraint_violation else None,
            "escalation_reason": self.escalation_reason,
            "escalation_target": self.escalation_target,
            "ssf_id": str(self.ssf_id) if self.ssf_id else None,
            "ssf_name": self.ssf_name,
            "invoked_at": self.invoked_at.isoformat(),
        }

    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.status == SSFStatus.SUCCESS


@dataclass
class SpawnConstraints:
    """
    Constraints on dynamic SSF spawning.

    When a persona has spawn permissions, these constraints limit
    what kinds of SSFs can be created.
    """
    # Allowed patterns
    permitted_categories: List[SSFCategory] = field(default_factory=list)
    permitted_handler_types: List[HandlerType] = field(default_factory=list)
    max_risk_level: RiskLevel = RiskLevel.MEDIUM

    # Forbidden operations
    forbidden_side_effects: List[str] = field(default_factory=list)
    forbidden_tools: List[str] = field(default_factory=list)

    # Resource limits
    max_timeout_seconds: int = 60
    max_memory_mb: int = 256

    # Spawning limits
    max_spawned_per_session: int = 10
    max_spawned_total: int = 100

    # Approval requirements
    requires_approval: bool = False
    approval_threshold: float = 0.8  # 0-1, consensus required

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "permitted_categories": [c.value for c in self.permitted_categories],
            "permitted_handler_types": [h.value for h in self.permitted_handler_types],
            "max_risk_level": self.max_risk_level.value,
            "forbidden_side_effects": self.forbidden_side_effects,
            "forbidden_tools": self.forbidden_tools,
            "max_timeout_seconds": self.max_timeout_seconds,
            "max_memory_mb": self.max_memory_mb,
            "max_spawned_per_session": self.max_spawned_per_session,
            "max_spawned_total": self.max_spawned_total,
            "requires_approval": self.requires_approval,
            "approval_threshold": self.approval_threshold,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SpawnConstraints":
        """Create from dictionary."""
        return cls(
            permitted_categories=[SSFCategory(c) for c in d.get("permitted_categories", [])],
            permitted_handler_types=[HandlerType(h) for h in d.get("permitted_handler_types", [])],
            max_risk_level=RiskLevel(d.get("max_risk_level", "medium")),
            forbidden_side_effects=d.get("forbidden_side_effects", []),
            forbidden_tools=d.get("forbidden_tools", []),
            max_timeout_seconds=d.get("max_timeout_seconds", 60),
            max_memory_mb=d.get("max_memory_mb", 256),
            max_spawned_per_session=d.get("max_spawned_per_session", 10),
            max_spawned_total=d.get("max_spawned_total", 100),
            requires_approval=d.get("requires_approval", False),
            approval_threshold=d.get("approval_threshold", 0.8),
        )

    @classmethod
    def restrictive(cls) -> "SpawnConstraints":
        """Create restrictive spawn constraints."""
        return cls(
            permitted_categories=[SSFCategory.COMPUTATION, SSFCategory.DATA_RETRIEVAL],
            permitted_handler_types=[HandlerType.MODULE],
            max_risk_level=RiskLevel.LOW,
            max_timeout_seconds=30,
            max_memory_mb=128,
            max_spawned_per_session=5,
            requires_approval=True,
        )

    @classmethod
    def permissive(cls) -> "SpawnConstraints":
        """Create permissive spawn constraints."""
        return cls(
            permitted_categories=list(SSFCategory),
            permitted_handler_types=[HandlerType.MODULE, HandlerType.MCP],
            max_risk_level=RiskLevel.HIGH,
            max_timeout_seconds=300,
            max_memory_mb=512,
            max_spawned_per_session=20,
            requires_approval=False,
        )


@dataclass
class SSFPermissions:
    """
    SSF-related permissions for a persona.

    Determines what SSFs a persona can invoke and spawn.
    """
    # Invocation permissions
    can_invoke_ssfs: bool = True
    permitted_categories: List[SSFCategory] = field(default_factory=list)  # Empty = all
    max_risk_level: RiskLevel = RiskLevel.HIGH
    blocked_ssf_ids: List[UUID] = field(default_factory=list)

    # Spawning permissions
    can_spawn_ssfs: bool = False
    spawn_constraints: Optional[SpawnConstraints] = None

    # Composition permissions
    can_compose_ssfs: bool = True
    max_composition_length: int = 10
    can_parallel_compose: bool = True
    max_parallel_ssfs: int = 5

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "can_invoke_ssfs": self.can_invoke_ssfs,
            "permitted_categories": [c.value for c in self.permitted_categories],
            "max_risk_level": self.max_risk_level.value,
            "blocked_ssf_ids": [str(id) for id in self.blocked_ssf_ids],
            "can_spawn_ssfs": self.can_spawn_ssfs,
            "spawn_constraints": self.spawn_constraints.to_dict() if self.spawn_constraints else None,
            "can_compose_ssfs": self.can_compose_ssfs,
            "max_composition_length": self.max_composition_length,
            "can_parallel_compose": self.can_parallel_compose,
            "max_parallel_ssfs": self.max_parallel_ssfs,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SSFPermissions":
        """Create from dictionary."""
        return cls(
            can_invoke_ssfs=d.get("can_invoke_ssfs", True),
            permitted_categories=[SSFCategory(c) for c in d.get("permitted_categories", [])],
            max_risk_level=RiskLevel(d.get("max_risk_level", "high")),
            blocked_ssf_ids=[UUID(id) for id in d.get("blocked_ssf_ids", [])],
            can_spawn_ssfs=d.get("can_spawn_ssfs", False),
            spawn_constraints=SpawnConstraints.from_dict(d["spawn_constraints"]) if d.get("spawn_constraints") else None,
            can_compose_ssfs=d.get("can_compose_ssfs", True),
            max_composition_length=d.get("max_composition_length", 10),
            can_parallel_compose=d.get("can_parallel_compose", True),
            max_parallel_ssfs=d.get("max_parallel_ssfs", 5),
        )

    @classmethod
    def default_servant(cls) -> "SSFPermissions":
        """Default permissions for servant personas."""
        return cls(
            can_invoke_ssfs=True,
            permitted_categories=[],  # All categories
            max_risk_level=RiskLevel.HIGH,
            can_spawn_ssfs=False,
            can_compose_ssfs=True,
            max_composition_length=10,
        )

    @classmethod
    def admin(cls) -> "SSFPermissions":
        """Admin permissions with full SSF access."""
        return cls(
            can_invoke_ssfs=True,
            permitted_categories=[],
            max_risk_level=RiskLevel.CRITICAL,
            can_spawn_ssfs=True,
            spawn_constraints=SpawnConstraints.permissive(),
            can_compose_ssfs=True,
            max_composition_length=50,
            can_parallel_compose=True,
            max_parallel_ssfs=10,
        )


@dataclass
class ExecutionContext:
    """
    Context for SSF execution.

    Contains runtime information about the execution environment,
    including request metadata, tracing info, and resource limits.
    """
    # Request metadata
    request_id: UUID = field(default_factory=uuid4)
    trace_id: Optional[str] = None
    parent_span_id: Optional[str] = None

    # Execution environment
    environment: str = "production"  # production, staging, development
    community_id: Optional[str] = None
    vessel_id: Optional[str] = None

    # Resource overrides
    timeout_override: Optional[int] = None
    memory_override: Optional[int] = None

    # Security context
    authenticated_user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "request_id": str(self.request_id),
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "environment": self.environment,
            "community_id": self.community_id,
            "vessel_id": self.vessel_id,
            "timeout_override": self.timeout_override,
            "memory_override": self.memory_override,
            "authenticated_user_id": self.authenticated_user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }


@dataclass
class SSFSpawnRequest:
    """Request to spawn a new SSF dynamically."""
    name: str
    description: str
    description_for_llm: str
    category: SSFCategory
    handler: SSFHandler
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    side_effects: List[str] = field(default_factory=list)
    timeout_seconds: int = 30
    memory_mb: int = 128

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "description_for_llm": self.description_for_llm,
            "category": self.category.value,
            "handler": self.handler.to_dict(),
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "tags": self.tags,
            "risk_level": self.risk_level.value,
            "side_effects": self.side_effects,
            "timeout_seconds": self.timeout_seconds,
            "memory_mb": self.memory_mb,
        }
