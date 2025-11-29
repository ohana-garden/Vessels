"""
Serverless Smart Function (SSF) System for Vessels.

SSFs are the mandatory execution layer through which ALL agent actions must pass.
This is the PRIMARY SAFETY MECHANISM that ensures ethical constraints are enforced
at runtime, not just at planning time.

The Safety Principle:
    Traditional AI agent systems have an escape hatch problem:
        Agent (constrained by ethics) -> External API (unconstrained) -> Harm

    Vessels inverts this:
        Persona (defines ethics) -> A0 Agent (reasoning) -> SSF (constrained execution) -> External World

    Every action an agent takes must pass through an SSF. SSFs inherit the ethical
    manifold position of their invoking persona. There is no raw code execution,
    no direct API calls, no escape hatch.

Architecture:
    - schema.py: Core data structures for SSF definitions
    - runtime.py: SSF execution engine with constraint binding
    - registry.py: SSF discovery, registration, and spawning
    - composition.py: SSF chaining and parallel execution
    - validation.py: Schema and constraint validation
    - logging.py: Execution logging to Graphiti
    - generator.py: LLM-powered SSF generation
    - builtins/: Library of built-in SSFs
"""

from .schema import (
    SSFDefinition,
    SSFCategory,
    RiskLevel,
    SSFHandler,
    HandlerType,
    ConstraintBindingConfig,
    ConstraintBindingMode,
    BoundaryBehavior,
    SSFResult,
    SSFStatus,
    SSFPermissions,
    SpawnConstraints,
)

from .runtime import SSFRuntime
from .registry import SSFRegistry
from .composition import SSFComposer, SSFStep, CompositionResult
from .validation import SSFValidator, ValidationResult

__all__ = [
    # Schema
    "SSFDefinition",
    "SSFCategory",
    "RiskLevel",
    "SSFHandler",
    "HandlerType",
    "ConstraintBindingConfig",
    "ConstraintBindingMode",
    "BoundaryBehavior",
    "SSFResult",
    "SSFStatus",
    "SSFPermissions",
    "SpawnConstraints",
    # Runtime
    "SSFRuntime",
    # Registry
    "SSFRegistry",
    # Composition
    "SSFComposer",
    "SSFStep",
    "CompositionResult",
    # Validation
    "SSFValidator",
    "ValidationResult",
]
