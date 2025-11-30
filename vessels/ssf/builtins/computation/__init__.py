"""
Computation SSFs - Data Transformation, Validation, Aggregation.

These SSFs handle pure computational operations with no external
side effects, making them safe for unconstrained execution.
"""

from typing import Dict, Any, List, Optional
from uuid import uuid4
import json
import logging

from ...schema import (
    SSFDefinition,
    SSFCategory,
    RiskLevel,
    SSFHandler,
    ConstraintBindingConfig,
)

logger = logging.getLogger(__name__)


# ============================================================================
# HANDLER IMPLEMENTATIONS
# ============================================================================

async def handle_transform_data(
    data: Any,
    transformation: str,
    options: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Transform data according to a transformation specification.

    Args:
        data: Input data to transform
        transformation: Transformation type (json_to_csv, flatten, etc.)
        options: Transformation options

    Returns:
        Transformed data
    """
    logger.info(f"Transforming data with {transformation}")

    options = options or {}

    if transformation == "flatten":
        result = _flatten_dict(data) if isinstance(data, dict) else data
    elif transformation == "json_to_string":
        result = json.dumps(data, indent=options.get("indent", 2))
    elif transformation == "extract_keys":
        result = list(data.keys()) if isinstance(data, dict) else []
    elif transformation == "count_items":
        result = len(data) if hasattr(data, "__len__") else 1
    else:
        result = data

    return {
        "result": result,
        "transformation": transformation,
        "input_type": type(data).__name__,
    }


async def handle_aggregate_results(
    results: List[Dict[str, Any]],
    aggregation: str = "merge",
    key_field: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Aggregate multiple results into a single output.

    Args:
        results: List of results to aggregate
        aggregation: Aggregation type (merge, list, group)
        key_field: Optional field to group by

    Returns:
        Aggregated result
    """
    logger.info(f"Aggregating {len(results)} results with {aggregation}")

    if aggregation == "merge":
        merged = {}
        for r in results:
            if isinstance(r, dict):
                merged.update(r)
        return {"result": merged, "count": len(results)}

    elif aggregation == "list":
        return {"result": results, "count": len(results)}

    elif aggregation == "group" and key_field:
        groups: Dict[str, List] = {}
        for r in results:
            if isinstance(r, dict) and key_field in r:
                key = str(r[key_field])
                if key not in groups:
                    groups[key] = []
                groups[key].append(r)
        return {"result": groups, "count": len(results), "groups": len(groups)}

    return {"result": results, "count": len(results)}


async def handle_format_output(
    data: Any,
    format_type: str = "text",
    template: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Format data for presentation.

    Args:
        data: Data to format
        format_type: Output format (text, markdown, json, html)
        template: Optional template string

    Returns:
        Formatted output
    """
    logger.info(f"Formatting data as {format_type}")

    if format_type == "json":
        formatted = json.dumps(data, indent=2, default=str)
    elif format_type == "markdown":
        formatted = _to_markdown(data)
    elif format_type == "text":
        formatted = str(data)
    elif format_type == "template" and template:
        formatted = template.format(**data) if isinstance(data, dict) else template.format(data=data)
    else:
        formatted = str(data)

    return {
        "formatted": formatted,
        "format_type": format_type,
    }


async def handle_validate_data(
    data: Any,
    schema: Dict[str, Any],
    strict: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Validate data against a JSON schema.

    Args:
        data: Data to validate
        schema: JSON Schema to validate against
        strict: Fail on additional properties

    Returns:
        Validation result
    """
    logger.info("Validating data against schema")

    errors = []
    valid = True

    # Basic type checking
    expected_type = schema.get("type")
    if expected_type:
        type_valid = _check_type(data, expected_type)
        if not type_valid:
            valid = False
            errors.append(f"Expected type {expected_type}, got {type(data).__name__}")

    # Check required fields for objects
    if expected_type == "object" and isinstance(data, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                valid = False
                errors.append(f"Missing required field: {field}")

        # Check properties
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                prop_schema = properties[key]
                prop_type = prop_schema.get("type")
                if prop_type and not _check_type(value, prop_type):
                    valid = False
                    errors.append(f"Field {key}: expected {prop_type}")

            elif strict and not schema.get("additionalProperties", True):
                valid = False
                errors.append(f"Unknown field: {key}")

    return {
        "valid": valid,
        "errors": errors,
        "error_count": len(errors),
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _flatten_dict(d: Dict, parent_key: str = "", sep: str = ".") -> Dict:
    """Flatten a nested dictionary."""
    items: List = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _to_markdown(data: Any, depth: int = 0) -> str:
    """Convert data to markdown format."""
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{'#' * (depth + 2)} {k}")
                lines.append(_to_markdown(v, depth + 1))
            else:
                lines.append(f"- **{k}**: {v}")
        return "\n".join(lines)
    elif isinstance(data, list):
        return "\n".join(f"- {_to_markdown(item, depth)}" for item in data)
    else:
        return str(data)


def _check_type(value: Any, expected: str) -> bool:
    """Check if value matches expected JSON type."""
    type_map = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }
    expected_type = type_map.get(expected)
    return isinstance(value, expected_type) if expected_type else True


# ============================================================================
# SSF DEFINITIONS
# ============================================================================

def _create_transform_data_ssf() -> SSFDefinition:
    """Create the transform_data SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="transform_data",
        version="1.0.0",
        category=SSFCategory.COMPUTATION,
        tags=["transform", "data", "convert", "process"],
        description="Transform data using various operations like flattening, extraction, or format conversion.",
        description_for_llm="Use this SSF to transform data structures. Supports flattening nested objects, extracting keys, counting items, and format conversion. Good for preparing data for other operations or formatting output.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.computation",
            function_name="handle_transform_data",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "data": {
                    "description": "Input data to transform",
                },
                "transformation": {
                    "type": "string",
                    "enum": ["flatten", "json_to_string", "extract_keys", "count_items"],
                    "description": "Transformation type",
                },
                "options": {
                    "type": "object",
                    "description": "Transformation options",
                },
            },
            "required": ["data", "transformation"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "result": {},
                "transformation": {"type": "string"},
                "input_type": {"type": "string"},
            },
        },
        timeout_seconds=30,
        memory_mb=256,
        risk_level=RiskLevel.LOW,
        side_effects=[],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def _create_aggregate_results_ssf() -> SSFDefinition:
    """Create the aggregate_results SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="aggregate_results",
        version="1.0.0",
        category=SSFCategory.COMPUTATION,
        tags=["aggregate", "combine", "merge", "collect"],
        description="Aggregate multiple results into a single combined output.",
        description_for_llm="Use this SSF to combine multiple results from parallel operations. Supports merging, listing, and grouping by key. Good for combining SSF composition results or aggregating data from multiple sources.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.computation",
            function_name="handle_aggregate_results",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Results to aggregate",
                },
                "aggregation": {
                    "type": "string",
                    "enum": ["merge", "list", "group"],
                    "default": "merge",
                    "description": "Aggregation type",
                },
                "key_field": {
                    "type": "string",
                    "description": "Field to group by (for group aggregation)",
                },
            },
            "required": ["results"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "result": {},
                "count": {"type": "integer"},
            },
        },
        timeout_seconds=30,
        memory_mb=256,
        risk_level=RiskLevel.LOW,
        side_effects=[],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def _create_format_output_ssf() -> SSFDefinition:
    """Create the format_output SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="format_output",
        version="1.0.0",
        category=SSFCategory.COMPUTATION,
        tags=["format", "output", "presentation", "display"],
        description="Format data for presentation in various output formats.",
        description_for_llm="Use this SSF to format data for display or output. Supports text, JSON, markdown, and templated formats. Good for preparing final output, generating reports, or formatting messages.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.computation",
            function_name="handle_format_output",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "data": {
                    "description": "Data to format",
                },
                "format_type": {
                    "type": "string",
                    "enum": ["text", "json", "markdown", "html", "template"],
                    "default": "text",
                    "description": "Output format",
                },
                "template": {
                    "type": "string",
                    "description": "Template string (for template format)",
                },
            },
            "required": ["data"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "formatted": {"type": "string"},
                "format_type": {"type": "string"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.LOW,
        side_effects=[],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def _create_validate_data_ssf() -> SSFDefinition:
    """Create the validate_data SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="validate_data",
        version="1.0.0",
        category=SSFCategory.COMPUTATION,
        tags=["validate", "schema", "check", "verify"],
        description="Validate data against a JSON schema to ensure correctness.",
        description_for_llm="Use this SSF to validate data structures against JSON schemas. Good for verifying inputs before processing, checking API responses, or ensuring data integrity.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.computation",
            function_name="handle_validate_data",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "data": {
                    "description": "Data to validate",
                },
                "schema": {
                    "type": "object",
                    "description": "JSON Schema to validate against",
                },
                "strict": {
                    "type": "boolean",
                    "default": False,
                    "description": "Fail on additional properties",
                },
            },
            "required": ["data", "schema"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "valid": {"type": "boolean"},
                "errors": {"type": "array"},
                "error_count": {"type": "integer"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.LOW,
        side_effects=[],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def get_builtin_ssfs() -> List[SSFDefinition]:
    """Get all built-in computation SSFs."""
    return [
        _create_transform_data_ssf(),
        _create_aggregate_results_ssf(),
        _create_format_output_ssf(),
        _create_validate_data_ssf(),
    ]
