"""
SSF Validation - Schema and Constraint Validation.

Validates SSF definitions for completeness, safety, and correctness.
Used both at registration time and for dynamic SSF spawning.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .schema import (
    SSFDefinition,
    SSFHandler,
    HandlerType,
    SSFCategory,
    RiskLevel,
    ConstraintBindingConfig,
    ConstraintBindingMode,
)

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Must be fixed before use
    WARNING = "warning"  # Should be fixed but not blocking
    INFO = "info"        # Informational suggestion


@dataclass
class ValidationIssue:
    """A single validation issue."""
    field: str
    message: str
    severity: ValidationSeverity
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of SSF validation."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "valid": self.valid,
            "issues": [i.to_dict() for i in self.issues],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "validated_at": self.validated_at.isoformat(),
        }


class SSFValidator:
    """
    Validates SSF definitions for completeness and safety.

    Checks:
    - Required fields are present
    - Handler is properly configured
    - Schemas are valid JSON Schema
    - Risk level matches side effects
    - Constraint binding is appropriate
    - No security issues in patterns
    """

    # Fields that must be non-empty
    REQUIRED_FIELDS = ["name", "description", "category"]

    # Dangerous patterns in inline code
    DANGEROUS_PATTERNS = [
        r"import\s+os",
        r"import\s+subprocess",
        r"import\s+sys",
        r"__import__",
        r"eval\s*\(",
        r"exec\s*\(",
        r"compile\s*\(",
        r"open\s*\(",
        r"file\s*\(",
        r"globals\s*\(",
        r"locals\s*\(",
        r"getattr\s*\(",
        r"setattr\s*\(",
        r"delattr\s*\(",
    ]

    def __init__(self):
        """Initialize the validator."""
        self._dangerous_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS
        ]

    def validate(self, ssf: SSFDefinition) -> ValidationResult:
        """
        Validate an SSF definition.

        Args:
            ssf: SSF definition to validate

        Returns:
            ValidationResult with any issues found
        """
        issues: List[ValidationIssue] = []

        # Validate required fields
        issues.extend(self._validate_required_fields(ssf))

        # Validate handler
        issues.extend(self._validate_handler(ssf))

        # Validate schemas
        issues.extend(self._validate_schemas(ssf))

        # Validate risk level consistency
        issues.extend(self._validate_risk_consistency(ssf))

        # Validate constraint binding
        issues.extend(self._validate_constraint_binding(ssf))

        # Validate resource limits
        issues.extend(self._validate_resource_limits(ssf))

        # Check for security issues
        issues.extend(self._validate_security(ssf))

        # Determine overall validity
        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)

        return ValidationResult(
            valid=not has_errors,
            issues=issues,
        )

    def _validate_required_fields(self, ssf: SSFDefinition) -> List[ValidationIssue]:
        """Validate required fields are present."""
        issues = []

        if not ssf.name:
            issues.append(ValidationIssue(
                field="name",
                message="SSF name is required",
                severity=ValidationSeverity.ERROR,
            ))
        elif not re.match(r'^[a-z][a-z0-9_]*$', ssf.name):
            issues.append(ValidationIssue(
                field="name",
                message="SSF name should be lowercase with underscores",
                severity=ValidationSeverity.WARNING,
                suggestion="Use snake_case format like 'send_sms'",
            ))

        if not ssf.description:
            issues.append(ValidationIssue(
                field="description",
                message="SSF description is required",
                severity=ValidationSeverity.ERROR,
            ))
        elif len(ssf.description) < 20:
            issues.append(ValidationIssue(
                field="description",
                message="SSF description is too short",
                severity=ValidationSeverity.WARNING,
                suggestion="Provide a more detailed description (20+ chars)",
            ))

        if not ssf.description_for_llm:
            issues.append(ValidationIssue(
                field="description_for_llm",
                message="LLM-optimized description is missing",
                severity=ValidationSeverity.INFO,
                suggestion="Add a description optimized for LLM tool selection",
            ))

        return issues

    def _validate_handler(self, ssf: SSFDefinition) -> List[ValidationIssue]:
        """Validate handler configuration."""
        issues = []

        if not ssf.handler:
            issues.append(ValidationIssue(
                field="handler",
                message="SSF handler is required",
                severity=ValidationSeverity.ERROR,
            ))
            return issues

        handler = ssf.handler

        if handler.type == HandlerType.INLINE:
            if not handler.inline_code:
                issues.append(ValidationIssue(
                    field="handler.inline_code",
                    message="Inline handler requires code",
                    severity=ValidationSeverity.ERROR,
                ))

        elif handler.type == HandlerType.MODULE:
            if not handler.module_path:
                issues.append(ValidationIssue(
                    field="handler.module_path",
                    message="Module handler requires module_path",
                    severity=ValidationSeverity.ERROR,
                ))
            if not handler.function_name:
                issues.append(ValidationIssue(
                    field="handler.function_name",
                    message="Module handler requires function_name",
                    severity=ValidationSeverity.ERROR,
                ))

        elif handler.type == HandlerType.MCP:
            if not handler.mcp_server:
                issues.append(ValidationIssue(
                    field="handler.mcp_server",
                    message="MCP handler requires mcp_server",
                    severity=ValidationSeverity.ERROR,
                ))
            if not handler.mcp_tool:
                issues.append(ValidationIssue(
                    field="handler.mcp_tool",
                    message="MCP handler requires mcp_tool",
                    severity=ValidationSeverity.ERROR,
                ))

        elif handler.type == HandlerType.REMOTE:
            if not handler.remote_url:
                issues.append(ValidationIssue(
                    field="handler.remote_url",
                    message="Remote handler requires remote_url",
                    severity=ValidationSeverity.ERROR,
                ))
            elif not handler.remote_url.startswith(('http://', 'https://')):
                issues.append(ValidationIssue(
                    field="handler.remote_url",
                    message="Remote URL must use HTTP(S)",
                    severity=ValidationSeverity.ERROR,
                ))

        elif handler.type == HandlerType.CONTAINER:
            if not handler.container_image:
                issues.append(ValidationIssue(
                    field="handler.container_image",
                    message="Container handler requires container_image",
                    severity=ValidationSeverity.ERROR,
                ))

        return issues

    def _validate_schemas(self, ssf: SSFDefinition) -> List[ValidationIssue]:
        """Validate input/output schemas."""
        issues = []

        # Validate input schema
        if ssf.input_schema:
            schema_issues = self._validate_json_schema(ssf.input_schema, "input_schema")
            issues.extend(schema_issues)
        else:
            issues.append(ValidationIssue(
                field="input_schema",
                message="Input schema is missing",
                severity=ValidationSeverity.WARNING,
                suggestion="Define input schema for better validation",
            ))

        # Validate output schema
        if ssf.output_schema:
            schema_issues = self._validate_json_schema(ssf.output_schema, "output_schema")
            issues.extend(schema_issues)
        else:
            issues.append(ValidationIssue(
                field="output_schema",
                message="Output schema is missing",
                severity=ValidationSeverity.INFO,
                suggestion="Define output schema for better documentation",
            ))

        return issues

    def _validate_json_schema(self, schema: Dict[str, Any], field_name: str) -> List[ValidationIssue]:
        """Validate a JSON Schema."""
        issues = []

        if not isinstance(schema, dict):
            issues.append(ValidationIssue(
                field=field_name,
                message="Schema must be an object",
                severity=ValidationSeverity.ERROR,
            ))
            return issues

        # Check for required type field
        if "type" not in schema:
            issues.append(ValidationIssue(
                field=field_name,
                message="Schema should have a 'type' field",
                severity=ValidationSeverity.WARNING,
            ))

        # If object type, check for properties
        if schema.get("type") == "object":
            if "properties" not in schema:
                issues.append(ValidationIssue(
                    field=field_name,
                    message="Object schema should define properties",
                    severity=ValidationSeverity.WARNING,
                ))

        return issues

    def _validate_risk_consistency(self, ssf: SSFDefinition) -> List[ValidationIssue]:
        """Validate risk level is consistent with SSF properties."""
        issues = []

        # Check if side effects match risk level
        has_side_effects = len(ssf.side_effects) > 0

        if ssf.risk_level == RiskLevel.LOW:
            if has_side_effects:
                issues.append(ValidationIssue(
                    field="risk_level",
                    message="Low-risk SSF has side effects declared",
                    severity=ValidationSeverity.WARNING,
                    suggestion="Consider raising risk level to MEDIUM or higher",
                ))
            if not ssf.reversible:
                issues.append(ValidationIssue(
                    field="risk_level",
                    message="Low-risk SSF marked as irreversible",
                    severity=ValidationSeverity.WARNING,
                    suggestion="Irreversible operations should be MEDIUM risk or higher",
                ))

        if ssf.risk_level == RiskLevel.CRITICAL:
            if not has_side_effects:
                issues.append(ValidationIssue(
                    field="side_effects",
                    message="Critical-risk SSF should document side effects",
                    severity=ValidationSeverity.WARNING,
                ))

        # Category-based risk suggestions
        high_risk_categories = [SSFCategory.COMMUNICATION, SSFCategory.DATA_MUTATION]
        if ssf.category in high_risk_categories and ssf.risk_level == RiskLevel.LOW:
            issues.append(ValidationIssue(
                field="risk_level",
                message=f"{ssf.category.value} SSF marked as low risk",
                severity=ValidationSeverity.INFO,
                suggestion="Consider if this SSF truly has no side effects",
            ))

        return issues

    def _validate_constraint_binding(self, ssf: SSFDefinition) -> List[ValidationIssue]:
        """Validate constraint binding configuration."""
        issues = []
        binding = ssf.constraint_binding

        # Check explicit mode has constraints
        if binding.mode == ConstraintBindingMode.EXPLICIT:
            if not binding.explicit_constraints:
                issues.append(ValidationIssue(
                    field="constraint_binding.explicit_constraints",
                    message="Explicit mode requires explicit_constraints list",
                    severity=ValidationSeverity.ERROR,
                ))

        # Check escalation target for escalate mode
        if binding.on_boundary_approach.value == "escalate":
            if not binding.escalation_target:
                issues.append(ValidationIssue(
                    field="constraint_binding.escalation_target",
                    message="Escalate mode should specify escalation_target",
                    severity=ValidationSeverity.WARNING,
                ))

        # Validate forbidden patterns
        for i, pattern in enumerate(binding.forbidden_input_patterns):
            try:
                re.compile(pattern)
            except re.error as e:
                issues.append(ValidationIssue(
                    field=f"constraint_binding.forbidden_input_patterns[{i}]",
                    message=f"Invalid regex pattern: {e}",
                    severity=ValidationSeverity.ERROR,
                ))

        for i, pattern in enumerate(binding.forbidden_output_patterns):
            try:
                re.compile(pattern)
            except re.error as e:
                issues.append(ValidationIssue(
                    field=f"constraint_binding.forbidden_output_patterns[{i}]",
                    message=f"Invalid regex pattern: {e}",
                    severity=ValidationSeverity.ERROR,
                ))

        # Validate boundary threshold
        if not 0 <= binding.boundary_threshold <= 1:
            issues.append(ValidationIssue(
                field="constraint_binding.boundary_threshold",
                message="Boundary threshold must be between 0 and 1",
                severity=ValidationSeverity.ERROR,
            ))

        return issues

    def _validate_resource_limits(self, ssf: SSFDefinition) -> List[ValidationIssue]:
        """Validate resource limits."""
        issues = []

        if ssf.timeout_seconds < 1:
            issues.append(ValidationIssue(
                field="timeout_seconds",
                message="Timeout must be at least 1 second",
                severity=ValidationSeverity.ERROR,
            ))
        elif ssf.timeout_seconds > 900:
            issues.append(ValidationIssue(
                field="timeout_seconds",
                message="Timeout exceeds maximum (900 seconds)",
                severity=ValidationSeverity.ERROR,
            ))
        elif ssf.timeout_seconds > 300:
            issues.append(ValidationIssue(
                field="timeout_seconds",
                message="Long timeout may indicate design issue",
                severity=ValidationSeverity.INFO,
                suggestion="Consider breaking into smaller SSFs",
            ))

        if ssf.memory_mb < 64:
            issues.append(ValidationIssue(
                field="memory_mb",
                message="Memory must be at least 64 MB",
                severity=ValidationSeverity.ERROR,
            ))
        elif ssf.memory_mb > 3008:
            issues.append(ValidationIssue(
                field="memory_mb",
                message="Memory exceeds maximum (3008 MB)",
                severity=ValidationSeverity.ERROR,
            ))

        return issues

    def _validate_security(self, ssf: SSFDefinition) -> List[ValidationIssue]:
        """Validate for security issues."""
        issues = []

        # Check inline code for dangerous patterns
        if ssf.handler and ssf.handler.type == HandlerType.INLINE:
            code = ssf.handler.inline_code or ""
            for pattern in self._dangerous_patterns:
                if pattern.search(code):
                    issues.append(ValidationIssue(
                        field="handler.inline_code",
                        message=f"Potentially dangerous pattern: {pattern.pattern}",
                        severity=ValidationSeverity.WARNING,
                        suggestion="Review inline code for security implications",
                    ))

        # Check for sensitive data patterns in descriptions
        sensitive_patterns = [r"password", r"secret", r"api.?key", r"token"]
        for pattern in sensitive_patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            if regex.search(ssf.description):
                issues.append(ValidationIssue(
                    field="description",
                    message=f"Description may contain sensitive info: {pattern}",
                    severity=ValidationSeverity.INFO,
                    suggestion="Ensure no actual secrets in description",
                ))

        return issues

    def suggest_improvements(
        self,
        ssf: SSFDefinition,
        usage_history: Optional[List[Dict[str, Any]]] = None
    ) -> List[ValidationIssue]:
        """
        Suggest improvements based on SSF definition and usage.

        Args:
            ssf: SSF to analyze
            usage_history: Optional list of past execution records

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Add tags if missing
        if not ssf.tags:
            suggestions.append(ValidationIssue(
                field="tags",
                message="SSF has no tags",
                severity=ValidationSeverity.INFO,
                suggestion=f"Add tags like '{ssf.category.value}', '{ssf.name.split('_')[0]}'",
            ))

        # Check for LLM description
        if not ssf.description_for_llm:
            suggestions.append(ValidationIssue(
                field="description_for_llm",
                message="Missing LLM-optimized description",
                severity=ValidationSeverity.INFO,
                suggestion="Add a description that helps AI select this SSF",
            ))
        elif len(ssf.description_for_llm) < 50:
            suggestions.append(ValidationIssue(
                field="description_for_llm",
                message="LLM description may be too brief",
                severity=ValidationSeverity.INFO,
                suggestion="Include use cases and example scenarios",
            ))

        # Analyze usage history if provided
        if usage_history:
            # Check for frequent errors
            error_count = sum(1 for h in usage_history if h.get("status") != "success")
            if error_count > len(usage_history) * 0.2:
                suggestions.append(ValidationIssue(
                    field="handler",
                    message=f"High error rate: {error_count}/{len(usage_history)} executions failed",
                    severity=ValidationSeverity.WARNING,
                    suggestion="Review handler implementation for reliability",
                ))

            # Check for slow executions
            times = [h.get("duration", 0) for h in usage_history if h.get("duration")]
            if times:
                avg_time = sum(times) / len(times)
                if avg_time > ssf.timeout_seconds * 0.5:
                    suggestions.append(ValidationIssue(
                        field="timeout_seconds",
                        message=f"Average execution time ({avg_time:.1f}s) is close to timeout",
                        severity=ValidationSeverity.WARNING,
                        suggestion="Consider increasing timeout or optimizing handler",
                    ))

        return suggestions
