"""
SSF Generator - LLM-Powered SSF Generation.

Generates high-quality SSF definitions and implementations using LLMs.
Used for:
1. Helping developers create new SSFs
2. A0 agents spawning SSFs dynamically (with constraints)

Generated SSFs are:
- Stateless (no side effects beyond declared ones)
- Atomic (single, well-defined operation)
- Idempotent where possible
- Well-documented
- Properly constrained
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from .schema import (
    SSFDefinition,
    SSFCategory,
    RiskLevel,
    SSFHandler,
    HandlerType,
    ConstraintBindingConfig,
)
from .validation import SSFValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class GenerationRequest:
    """Request to generate an SSF."""
    description: str
    category: Optional[SSFCategory] = None
    example_inputs: Optional[List[Dict[str, Any]]] = None
    example_outputs: Optional[List[Dict[str, Any]]] = None
    constraints: Optional[List[str]] = None
    handler_type: HandlerType = HandlerType.MODULE

    # Generation options
    generate_handler_code: bool = True
    generate_tests: bool = False
    strict_mode: bool = True  # Enforce best practices


@dataclass
class GeneratedSSF:
    """Result of SSF generation."""
    definition: SSFDefinition
    handler_code: Optional[str] = None
    test_code: Optional[str] = None
    validation_result: Optional[ValidationResult] = None
    generation_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "definition": self.definition.to_dict(),
            "handler_code": self.handler_code,
            "test_code": self.test_code,
            "validation_result": self.validation_result.to_dict() if self.validation_result else None,
            "generation_notes": self.generation_notes,
        }


class SSFGenerator:
    """
    Generates high-quality SSF definitions and implementations.

    Uses LLMs to:
    - Parse natural language descriptions
    - Infer appropriate schemas
    - Generate handler code
    - Create documentation
    - Suggest improvements
    """

    # Template for SSF generation prompt
    GENERATION_PROMPT_TEMPLATE = """You are an expert at creating Serverless Smart Functions (SSFs) for the Vessels agent framework.

SSFs are stateless, atomic execution units with these requirements:
- Stateless: No hidden state, all state in inputs/outputs
- Atomic: Single, well-defined operation
- Idempotent: Same inputs produce same outputs where possible
- Well-documented: Clear descriptions for humans and LLMs
- Properly constrained: Appropriate risk levels and bindings

Given this description: "{description}"

{examples_section}

Generate an SSF definition with:
1. A snake_case name (e.g., send_sms, query_database)
2. A clear description (2-3 sentences)
3. An LLM-optimized description for tool selection
4. Appropriate category: {categories}
5. Risk level: low, medium, high, or critical
6. Input JSON Schema with all required fields
7. Output JSON Schema
8. List of side effects (empty if read-only)
9. Whether effects are reversible

Return a JSON object with this structure:
{{
    "name": "string",
    "description": "string",
    "description_for_llm": "string",
    "category": "string",
    "risk_level": "string",
    "input_schema": {{}},
    "output_schema": {{}},
    "side_effects": [],
    "reversible": true,
    "tags": []
}}

JSON:"""

    HANDLER_CODE_PROMPT_TEMPLATE = """You are an expert Python developer creating handler code for an SSF.

SSF Definition:
- Name: {name}
- Description: {description}
- Input Schema: {input_schema}
- Output Schema: {output_schema}
- Category: {category}

Requirements:
- Function must be async
- Function must accept **kwargs for inputs
- Function must return a dictionary matching the output schema
- No global state or side effects beyond what's declared
- Include proper error handling
- Include type hints

Generate a Python function named `{function_name}`:

```python
async def {function_name}(**kwargs):
    # Implementation here
    pass
```

Python code:"""

    def __init__(
        self,
        llm_call: Optional[Callable[[str], str]] = None,
        validator: Optional[SSFValidator] = None,
    ):
        """
        Initialize the SSF generator.

        Args:
            llm_call: Function to call LLM with a prompt
            validator: Optional validator for generated SSFs
        """
        self.llm_call = llm_call
        self.validator = validator or SSFValidator()

    async def generate_from_description(
        self,
        request: GenerationRequest,
    ) -> GeneratedSSF:
        """
        Generate an SSF definition from natural language description.

        Args:
            request: Generation request with description and options

        Returns:
            GeneratedSSF with definition and optional code
        """
        notes: List[str] = []

        # Generate the SSF definition
        definition = await self._generate_definition(request)
        notes.append(f"Generated SSF: {definition.name}")

        # Generate handler code if requested
        handler_code = None
        if request.generate_handler_code:
            handler_code = await self._generate_handler_code(definition, request)
            notes.append("Generated handler code")

        # Generate tests if requested
        test_code = None
        if request.generate_tests:
            test_code = await self._generate_test_code(definition, handler_code)
            notes.append("Generated test code")

        # Validate the generated SSF
        validation = self.validator.validate(definition)
        if not validation.valid:
            notes.append(f"Validation issues: {len(validation.errors)} errors")

        return GeneratedSSF(
            definition=definition,
            handler_code=handler_code,
            test_code=test_code,
            validation_result=validation,
            generation_notes=notes,
        )

    async def _generate_definition(
        self,
        request: GenerationRequest,
    ) -> SSFDefinition:
        """Generate SSF definition using LLM."""
        # Build examples section
        examples_section = ""
        if request.example_inputs:
            examples_section += "\nExample inputs:\n"
            for i, ex in enumerate(request.example_inputs[:3]):
                examples_section += f"  {i+1}. {json.dumps(ex)}\n"

        if request.example_outputs:
            examples_section += "\nExpected outputs:\n"
            for i, ex in enumerate(request.example_outputs[:3]):
                examples_section += f"  {i+1}. {json.dumps(ex)}\n"

        # Build prompt
        categories = ", ".join([c.value for c in SSFCategory])
        prompt = self.GENERATION_PROMPT_TEMPLATE.format(
            description=request.description,
            examples_section=examples_section,
            categories=categories,
        )

        # Call LLM
        if self.llm_call:
            response = self.llm_call(prompt)
            definition_data = self._parse_json_response(response)
        else:
            # Fallback: generate basic definition without LLM
            definition_data = self._generate_basic_definition(request)

        # Apply overrides from request
        if request.category:
            definition_data["category"] = request.category.value

        # Create the SSF definition
        return self._create_definition_from_data(definition_data, request)

    async def _generate_handler_code(
        self,
        definition: SSFDefinition,
        request: GenerationRequest,
    ) -> str:
        """Generate handler implementation code."""
        function_name = f"handle_{definition.name}"

        prompt = self.HANDLER_CODE_PROMPT_TEMPLATE.format(
            name=definition.name,
            description=definition.description,
            input_schema=json.dumps(definition.input_schema, indent=2),
            output_schema=json.dumps(definition.output_schema, indent=2),
            category=definition.category.value,
            function_name=function_name,
        )

        if self.llm_call:
            response = self.llm_call(prompt)
            code = self._extract_code_block(response)
        else:
            # Fallback: generate stub code
            code = self._generate_stub_code(definition, function_name)

        return code

    async def _generate_test_code(
        self,
        definition: SSFDefinition,
        handler_code: Optional[str],
    ) -> str:
        """Generate test code for the SSF."""
        test_template = '''"""Tests for {name} SSF."""

import pytest
from uuid import uuid4

from vessels.ssf.runtime import SSFRuntime
from vessels.ssf.schema import SSFResult, SSFStatus


class Test{class_name}:
    """Tests for {name} SSF."""

    @pytest.fixture
    def runtime(self):
        """Create SSF runtime for testing."""
        return SSFRuntime()

    @pytest.mark.asyncio
    async def test_basic_invocation(self, runtime):
        """Test basic SSF invocation."""
        # TODO: Add test inputs
        inputs = {{}}

        # TODO: Mock dependencies

        # Invoke SSF
        # result = await runtime.invoke(...)

        # Assert success
        # assert result.status == SSFStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_input_validation(self, runtime):
        """Test that invalid inputs are rejected."""
        # TODO: Add invalid inputs
        pass

    @pytest.mark.asyncio
    async def test_constraint_validation(self, runtime):
        """Test that constraint violations are blocked."""
        # TODO: Add constraint violation test
        pass
'''

        class_name = "".join(word.title() for word in definition.name.split("_"))

        return test_template.format(
            name=definition.name,
            class_name=class_name,
        )

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        # Try to find JSON object in response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback to basic parsing
        return {}

    def _extract_code_block(self, response: str) -> str:
        """Extract code block from LLM response."""
        # Try to find Python code block
        code_match = re.search(r'```python\n([\s\S]*?)\n```', response)
        if code_match:
            return code_match.group(1)

        # Try generic code block
        code_match = re.search(r'```\n([\s\S]*?)\n```', response)
        if code_match:
            return code_match.group(1)

        # Return raw response if no code block found
        return response

    def _generate_basic_definition(self, request: GenerationRequest) -> Dict[str, Any]:
        """Generate basic definition without LLM."""
        # Extract name from description
        words = request.description.lower().split()
        name = "_".join(words[:3])[:30]

        # Infer category
        category = request.category or self._infer_category(request.description)

        # Infer risk level
        risk_level = self._infer_risk_level(request.description, category)

        # Build basic input schema from examples
        input_schema = {"type": "object", "properties": {}}
        if request.example_inputs:
            for ex in request.example_inputs:
                for key, value in ex.items():
                    input_schema["properties"][key] = {
                        "type": self._infer_json_type(value)
                    }

        return {
            "name": name,
            "description": request.description,
            "description_for_llm": f"Use this SSF when you need to {request.description.lower()}",
            "category": category.value,
            "risk_level": risk_level.value,
            "input_schema": input_schema,
            "output_schema": {"type": "object", "properties": {"result": {"type": "object"}}},
            "side_effects": [],
            "reversible": True,
            "tags": [],
        }

    def _create_definition_from_data(
        self,
        data: Dict[str, Any],
        request: GenerationRequest,
    ) -> SSFDefinition:
        """Create SSFDefinition from parsed data."""
        # Determine constraint binding based on category and risk
        category = SSFCategory(data.get("category", "computation"))
        risk_level = RiskLevel(data.get("risk_level", "low"))

        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            constraint_binding = ConstraintBindingConfig.strict()
        else:
            constraint_binding = ConstraintBindingConfig.permissive()

        # Create handler based on type
        handler = None
        if request.handler_type == HandlerType.MODULE:
            handler = SSFHandler.module(
                module_path=f"vessels.ssf.generated.{data.get('name', 'unknown')}",
                function_name=f"handle_{data.get('name', 'unknown')}",
            )
        elif request.handler_type == HandlerType.INLINE:
            handler = SSFHandler.inline("result = {'status': 'not_implemented'}")

        return SSFDefinition(
            id=uuid4(),
            name=data.get("name", "generated_ssf"),
            version="1.0.0",
            category=category,
            tags=data.get("tags", []),
            description=data.get("description", request.description),
            description_for_llm=data.get("description_for_llm", ""),
            handler=handler,
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
            risk_level=risk_level,
            side_effects=data.get("side_effects", []),
            reversible=data.get("reversible", True),
            constraint_binding=constraint_binding,
        )

    def _generate_stub_code(self, definition: SSFDefinition, function_name: str) -> str:
        """Generate stub handler code."""
        params = []
        for prop in definition.input_schema.get("properties", {}).keys():
            params.append(f"    {prop} = kwargs.get('{prop}')")

        params_str = "\n".join(params) if params else "    pass  # No parameters"

        return f'''async def {function_name}(**kwargs):
    """
    {definition.description}

    Args:
        **kwargs: Input parameters matching the input schema

    Returns:
        Dictionary matching the output schema
    """
{params_str}

    # TODO: Implement handler logic
    result = {{
        "status": "success",
        "message": "Not yet implemented"
    }}

    return result
'''

    def _infer_category(self, description: str) -> SSFCategory:
        """Infer category from description."""
        desc_lower = description.lower()

        category_keywords = {
            SSFCategory.COMMUNICATION: ["send", "email", "sms", "message", "notify"],
            SSFCategory.DATA_RETRIEVAL: ["get", "fetch", "query", "retrieve", "read", "search"],
            SSFCategory.DATA_MUTATION: ["create", "update", "delete", "write", "store", "save"],
            SSFCategory.SCHEDULING: ["schedule", "calendar", "appointment", "remind"],
            SSFCategory.EXTERNAL_API: ["api", "http", "rest", "webhook"],
            SSFCategory.AGENT_COORDINATION: ["delegate", "agent", "coordinate", "orchestrate"],
            SSFCategory.MEMORY_OPERATIONS: ["memory", "remember", "recall", "graphiti"],
            SSFCategory.FILE_OPERATIONS: ["file", "upload", "download"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                return category

        return SSFCategory.COMPUTATION

    def _infer_risk_level(
        self,
        description: str,
        category: SSFCategory
    ) -> RiskLevel:
        """Infer risk level from description and category."""
        desc_lower = description.lower()

        # High-risk keywords
        if any(kw in desc_lower for kw in ["delete", "send", "publish", "execute", "pay"]):
            return RiskLevel.HIGH

        # Critical keywords
        if any(kw in desc_lower for kw in ["financial", "health", "safety", "critical"]):
            return RiskLevel.CRITICAL

        # Category-based defaults
        category_risk = {
            SSFCategory.COMMUNICATION: RiskLevel.HIGH,
            SSFCategory.DATA_MUTATION: RiskLevel.MEDIUM,
            SSFCategory.DATA_RETRIEVAL: RiskLevel.LOW,
            SSFCategory.COMPUTATION: RiskLevel.LOW,
        }

        return category_risk.get(category, RiskLevel.MEDIUM)

    def _infer_json_type(self, value: Any) -> str:
        """Infer JSON Schema type from Python value."""
        if isinstance(value, str):
            return "string"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "string"

    async def suggest_improvements(
        self,
        ssf: SSFDefinition,
        usage_history: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """
        Suggest improvements to an SSF.

        Args:
            ssf: SSF to analyze
            usage_history: Optional usage history for analysis

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Run validation
        validation = self.validator.validate(ssf)
        for issue in validation.issues:
            if issue.suggestion:
                suggestions.append(issue.suggestion)

        # Add improvement suggestions
        improvements = self.validator.suggest_improvements(ssf, usage_history)
        for improvement in improvements:
            if improvement.suggestion:
                suggestions.append(improvement.suggestion)

        # LLM-based suggestions
        if self.llm_call:
            llm_suggestions = await self._get_llm_suggestions(ssf, usage_history)
            suggestions.extend(llm_suggestions)

        return suggestions

    async def _get_llm_suggestions(
        self,
        ssf: SSFDefinition,
        usage_history: Optional[List[Dict[str, Any]]],
    ) -> List[str]:
        """Get improvement suggestions from LLM."""
        prompt = f"""Analyze this SSF and suggest improvements:

Name: {ssf.name}
Description: {ssf.description}
Category: {ssf.category.value}
Risk Level: {ssf.risk_level.value}
Side Effects: {ssf.side_effects}

Suggest 2-3 specific improvements for:
- Better descriptions
- More appropriate risk level
- Better constraint binding
- Code quality improvements

Return suggestions as a numbered list."""

        try:
            response = self.llm_call(prompt)
            # Parse numbered list
            suggestions = []
            for line in response.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    # Remove numbering/bullets
                    suggestion = re.sub(r'^[\d\.\-\)\s]+', '', line).strip()
                    if suggestion:
                        suggestions.append(suggestion)
            return suggestions[:5]
        except Exception as e:
            logger.warning(f"LLM suggestions failed: {e}")
            return []
