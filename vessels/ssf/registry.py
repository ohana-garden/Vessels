"""
SSF Registry - Discovery, Registration, and Spawning.

The registry manages the catalog of available SSFs:
- Built-in SSFs shipped with Vessels
- Community-defined SSFs created by admins
- Dynamically spawned SSFs created by agents with spawn permissions

All SSFs are stored in the knowledge graph for semantic discovery.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4

from .schema import (
    SSFDefinition,
    SSFCategory,
    RiskLevel,
    HandlerType,
    SSFHandler,
    ConstraintBindingConfig,
    ConstraintBindingMode,
    BoundaryBehavior,
    SpawnConstraints,
    SSFSpawnRequest,
    SSFPermissions,
)

logger = logging.getLogger(__name__)


class SSFSpawnDeniedError(Exception):
    """SSF spawn request was denied."""
    pass


class SSFRegistrationError(Exception):
    """Error registering an SSF."""
    pass


@dataclass
class SSFMatch:
    """A matching SSF from a capability search."""
    ssf: SSFDefinition
    score: float  # 0-1 match score
    match_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "ssf_id": str(self.ssf.id),
            "ssf_name": self.ssf.name,
            "description": self.ssf.description,
            "category": self.ssf.category.value,
            "risk_level": self.ssf.risk_level.value,
            "score": self.score,
            "match_reasons": self.match_reasons,
        }


@dataclass
class Persona:
    """Minimal persona interface for registry."""
    id: UUID
    name: str
    community_id: str
    ssf_permissions: SSFPermissions = field(default_factory=SSFPermissions)


@dataclass
class A0AgentInstance:
    """Minimal agent interface for registry."""
    agent_id: str
    persona_id: UUID


class SSFRegistry:
    """
    Registry of available SSFs.

    SSFs can be:
    - Built-in (shipped with Vessels)
    - Community-defined (created by community admins)
    - Dynamically spawned (created by A0 agents with spawn permissions)

    The registry supports:
    - Semantic search for capability discovery
    - Permission-aware filtering
    - Dynamic SSF spawning with constraints
    - Graph-based storage for persistence
    """

    def __init__(
        self,
        graph_client: Optional[Any] = None,
        llm_call: Optional[Callable[[str], str]] = None,
    ):
        """
        Initialize the SSF registry.

        Args:
            graph_client: Optional Graphiti client for persistence
            llm_call: Optional LLM function for semantic search
        """
        self.graph_client = graph_client
        self.llm_call = llm_call

        # In-memory storage (primary when no graph, cache when graph exists)
        self._ssfs: Dict[UUID, SSFDefinition] = {}
        self._by_name: Dict[str, UUID] = {}
        self._by_category: Dict[SSFCategory, Set[UUID]] = {cat: set() for cat in SSFCategory}

        # Track spawned SSFs
        self._spawned_by_persona: Dict[UUID, List[UUID]] = {}
        self._spawn_counts: Dict[UUID, int] = {}  # session spawn counts

        # Pending approvals
        self._pending_approvals: Dict[UUID, SSFDefinition] = {}

    async def get(self, ssf_id: UUID) -> Optional[SSFDefinition]:
        """
        Retrieve SSF definition by ID.

        Args:
            ssf_id: UUID of the SSF

        Returns:
            SSFDefinition or None if not found
        """
        # Check memory cache first
        if ssf_id in self._ssfs:
            return self._ssfs[ssf_id]

        # Try graph if available
        if self.graph_client:
            ssf_data = await self._load_from_graph(ssf_id)
            if ssf_data:
                ssf = SSFDefinition.from_dict(ssf_data)
                self._cache_ssf(ssf)
                return ssf

        return None

    async def get_by_name(self, name: str) -> Optional[SSFDefinition]:
        """
        Retrieve SSF definition by name.

        Args:
            name: Name of the SSF

        Returns:
            SSFDefinition or None if not found
        """
        if name in self._by_name:
            return await self.get(self._by_name[name])
        return None

    async def register(self, ssf: SSFDefinition) -> UUID:
        """
        Register a new SSF in the registry.

        Args:
            ssf: SSF definition to register

        Returns:
            UUID of the registered SSF
        """
        # Validate the SSF
        if not ssf.name:
            raise SSFRegistrationError("SSF must have a name")

        if ssf.name in self._by_name:
            existing_id = self._by_name[ssf.name]
            if existing_id != ssf.id:
                raise SSFRegistrationError(f"SSF with name '{ssf.name}' already exists")

        # Store in memory
        self._cache_ssf(ssf)

        # Persist to graph if available
        if self.graph_client:
            await self._save_to_graph(ssf)

        logger.info(f"Registered SSF: {ssf.name} ({ssf.id})")
        return ssf.id

    async def unregister(self, ssf_id: UUID) -> bool:
        """
        Remove an SSF from the registry.

        Args:
            ssf_id: UUID of the SSF to remove

        Returns:
            True if removed, False if not found
        """
        if ssf_id not in self._ssfs:
            return False

        ssf = self._ssfs[ssf_id]

        # Remove from caches
        del self._ssfs[ssf_id]
        if ssf.name in self._by_name:
            del self._by_name[ssf.name]
        if ssf.category in self._by_category:
            self._by_category[ssf.category].discard(ssf_id)

        # Remove from graph if available
        if self.graph_client:
            await self._delete_from_graph(ssf_id)

        logger.info(f"Unregistered SSF: {ssf.name} ({ssf_id})")
        return True

    async def find_for_capability(
        self,
        capability_description: str,
        invoking_persona: Optional[Persona] = None,
        required_inputs: Optional[Dict[str, Any]] = None,
        max_results: int = 5,
    ) -> List[SSFMatch]:
        """
        Find SSFs that can fulfill a capability request.

        Used by A0 agents when deciding which SSF to invoke.
        Returns only SSFs the persona has permission to use.

        Args:
            capability_description: Natural language description of needed capability
            invoking_persona: Persona to filter permissions for
            required_inputs: Optional inputs the caller has available
            max_results: Maximum number of results to return

        Returns:
            List of SSFMatch objects sorted by score
        """
        matches = []

        for ssf in self._ssfs.values():
            # Filter by persona permissions
            if invoking_persona and not self._persona_can_invoke(ssf, invoking_persona):
                continue

            # Score the match
            score = ssf.matches_need(capability_description)
            match_reasons = []

            # Check name match
            if capability_description.lower() in ssf.name.lower():
                score += 0.3
                match_reasons.append("name_match")

            # Check description match
            if capability_description.lower() in ssf.description.lower():
                score += 0.2
                match_reasons.append("description_match")

            # Check tags match
            for tag in ssf.tags:
                if tag.lower() in capability_description.lower():
                    score += 0.1
                    match_reasons.append(f"tag:{tag}")

            # Check LLM description
            if ssf.description_for_llm:
                if capability_description.lower() in ssf.description_for_llm.lower():
                    score += 0.15
                    match_reasons.append("llm_description_match")

            if score > 0.1:
                matches.append(SSFMatch(
                    ssf=ssf,
                    score=min(score, 1.0),
                    match_reasons=match_reasons,
                ))

        # Use LLM for semantic ranking if available
        if self.llm_call and matches:
            matches = await self._llm_rank_matches(capability_description, matches)

        # Sort by score
        matches.sort(key=lambda m: m.score, reverse=True)

        return matches[:max_results]

    async def find_by_category(
        self,
        category: SSFCategory,
        invoking_persona: Optional[Persona] = None,
    ) -> List[SSFDefinition]:
        """
        Find all SSFs in a category.

        Args:
            category: SSF category to search
            invoking_persona: Optional persona for permission filtering

        Returns:
            List of SSF definitions
        """
        ssf_ids = self._by_category.get(category, set())
        results = []

        for ssf_id in ssf_ids:
            ssf = self._ssfs.get(ssf_id)
            if ssf:
                if invoking_persona and not self._persona_can_invoke(ssf, invoking_persona):
                    continue
                results.append(ssf)

        return results

    async def spawn(
        self,
        request: SSFSpawnRequest,
        invoking_persona: Persona,
        invoking_agent: A0AgentInstance,
    ) -> SSFDefinition:
        """
        Dynamically create a new SSF.

        This is A0's "dynamic tool creation" capability, but constrained:
        - Persona must have spawn permissions
        - New SSF inherits invoking persona's constraint manifold
        - SpawnConstraints limit what can be created
        - May require approval before activation

        Args:
            request: SSF spawn request
            invoking_persona: Persona spawning the SSF
            invoking_agent: Agent instance spawning the SSF

        Returns:
            Created SSF definition

        Raises:
            SSFSpawnDeniedError if spawn is not allowed
        """
        permissions = invoking_persona.ssf_permissions

        # 1. Check spawn permissions
        if not permissions.can_spawn_ssfs:
            raise SSFSpawnDeniedError("Persona lacks SSF spawn permission")

        spawn_constraints = permissions.spawn_constraints
        if not spawn_constraints:
            spawn_constraints = SpawnConstraints.restrictive()

        # 2. Validate against spawn constraints
        self._validate_spawn_request(request, spawn_constraints)

        # 3. Check spawn limits
        persona_spawns = self._spawn_counts.get(invoking_persona.id, 0)
        if persona_spawns >= spawn_constraints.max_spawned_per_session:
            raise SSFSpawnDeniedError(
                f"Spawn limit reached ({persona_spawns}/{spawn_constraints.max_spawned_per_session})"
            )

        # 4. Force constraint inheritance (spawned SSFs always inherit full constraints)
        constraint_binding = ConstraintBindingConfig(
            mode=ConstraintBindingMode.FULL,
            validate_inputs=True,
            validate_outputs=True,
            on_boundary_approach=BoundaryBehavior.ESCALATE,
        )

        # 5. Create the SSF definition
        ssf = SSFDefinition(
            id=uuid4(),
            name=request.name,
            version="1.0.0",
            category=request.category,
            tags=request.tags,
            description=request.description,
            description_for_llm=request.description_for_llm,
            handler=request.handler,
            input_schema=request.input_schema,
            output_schema=request.output_schema,
            timeout_seconds=min(request.timeout_seconds, spawn_constraints.max_timeout_seconds),
            memory_mb=min(request.memory_mb, spawn_constraints.max_memory_mb),
            risk_level=request.risk_level,
            side_effects=request.side_effects,
            reversible=True,  # Spawned SSFs should be reversible
            constraint_binding=constraint_binding,
            spawned_by=invoking_persona.id,
            spawned_at=datetime.utcnow(),
        )

        # 6. Check if approval required
        if spawn_constraints.requires_approval:
            self._pending_approvals[ssf.id] = ssf
            logger.info(f"SSF spawn pending approval: {ssf.name} ({ssf.id})")
            return ssf  # Return but don't register until approved

        # 7. Register the new SSF
        await self.register(ssf)

        # 8. Track spawning
        self._spawn_counts[invoking_persona.id] = persona_spawns + 1
        if invoking_persona.id not in self._spawned_by_persona:
            self._spawned_by_persona[invoking_persona.id] = []
        self._spawned_by_persona[invoking_persona.id].append(ssf.id)

        logger.info(f"SSF spawned: {ssf.name} by persona {invoking_persona.id}")
        return ssf

    async def approve_spawn(self, ssf_id: UUID, approver_id: str) -> Optional[SSFDefinition]:
        """
        Approve a pending SSF spawn.

        Args:
            ssf_id: ID of the SSF to approve
            approver_id: ID of the approving entity

        Returns:
            Approved SSF definition or None if not found
        """
        if ssf_id not in self._pending_approvals:
            return None

        ssf = self._pending_approvals.pop(ssf_id)
        await self.register(ssf)

        logger.info(f"SSF spawn approved: {ssf.name} by {approver_id}")
        return ssf

    async def reject_spawn(self, ssf_id: UUID, reason: str) -> bool:
        """
        Reject a pending SSF spawn.

        Args:
            ssf_id: ID of the SSF to reject
            reason: Reason for rejection

        Returns:
            True if rejected, False if not found
        """
        if ssf_id not in self._pending_approvals:
            return False

        ssf = self._pending_approvals.pop(ssf_id)
        logger.info(f"SSF spawn rejected: {ssf.name} - {reason}")
        return True

    def _validate_spawn_request(
        self,
        request: SSFSpawnRequest,
        constraints: SpawnConstraints
    ) -> None:
        """Validate a spawn request against constraints."""
        # Check category
        if constraints.permitted_categories:
            if request.category not in constraints.permitted_categories:
                raise SSFSpawnDeniedError(
                    f"Category {request.category.value} not permitted. "
                    f"Allowed: {[c.value for c in constraints.permitted_categories]}"
                )

        # Check handler type
        if constraints.permitted_handler_types:
            if request.handler.type not in constraints.permitted_handler_types:
                raise SSFSpawnDeniedError(
                    f"Handler type {request.handler.type.value} not permitted. "
                    f"Allowed: {[h.value for h in constraints.permitted_handler_types]}"
                )

        # Check risk level
        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        if risk_order.index(request.risk_level) > risk_order.index(constraints.max_risk_level):
            raise SSFSpawnDeniedError(
                f"Risk level {request.risk_level.value} exceeds max {constraints.max_risk_level.value}"
            )

        # Check forbidden side effects
        for effect in request.side_effects:
            for forbidden in constraints.forbidden_side_effects:
                if forbidden.lower() in effect.lower():
                    raise SSFSpawnDeniedError(f"Forbidden side effect: {effect}")

        # Check resource limits
        if request.timeout_seconds > constraints.max_timeout_seconds:
            raise SSFSpawnDeniedError(
                f"Timeout {request.timeout_seconds}s exceeds max {constraints.max_timeout_seconds}s"
            )

        if request.memory_mb > constraints.max_memory_mb:
            raise SSFSpawnDeniedError(
                f"Memory {request.memory_mb}MB exceeds max {constraints.max_memory_mb}MB"
            )

    def _persona_can_invoke(self, ssf: SSFDefinition, persona: Persona) -> bool:
        """Check if persona can invoke an SSF."""
        permissions = persona.ssf_permissions

        if not permissions.can_invoke_ssfs:
            return False

        if ssf.id in permissions.blocked_ssf_ids:
            return False

        if permissions.permitted_categories and ssf.category not in permissions.permitted_categories:
            return False

        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        if risk_order.index(ssf.risk_level) > risk_order.index(permissions.max_risk_level):
            return False

        return True

    def _cache_ssf(self, ssf: SSFDefinition) -> None:
        """Cache an SSF in memory."""
        self._ssfs[ssf.id] = ssf
        self._by_name[ssf.name] = ssf.id
        self._by_category[ssf.category].add(ssf.id)

    async def _load_from_graph(self, ssf_id: UUID) -> Optional[Dict[str, Any]]:
        """Load SSF from graph storage."""
        # Placeholder - would use Graphiti client
        return None

    async def _save_to_graph(self, ssf: SSFDefinition) -> None:
        """Save SSF to graph storage."""
        # Placeholder - would use Graphiti client
        pass

    async def _delete_from_graph(self, ssf_id: UUID) -> None:
        """Delete SSF from graph storage."""
        # Placeholder - would use Graphiti client
        pass

    async def _llm_rank_matches(
        self,
        capability: str,
        matches: List[SSFMatch]
    ) -> List[SSFMatch]:
        """Use LLM to rank matches semantically."""
        if not self.llm_call:
            return matches

        try:
            # Build prompt
            ssf_list = "\n".join([
                f"- {m.ssf.name}: {m.ssf.description}"
                for m in matches[:10]
            ])

            prompt = f"""Given this capability need: "{capability}"

Available SSFs:
{ssf_list}

Rank these SSFs from most to least relevant for this need.
Return just the names in order, one per line."""

            response = self.llm_call(prompt)

            # Parse response and reorder matches
            names_in_order = [line.strip().lstrip("- ") for line in response.strip().split("\n")]
            name_to_match = {m.ssf.name: m for m in matches}

            reordered = []
            for i, name in enumerate(names_in_order):
                if name in name_to_match:
                    match = name_to_match[name]
                    # Boost score based on LLM ranking
                    match.score = min(match.score * (1 + (len(names_in_order) - i) * 0.1), 1.0)
                    reordered.append(match)
                    del name_to_match[name]

            # Add any remaining matches
            reordered.extend(name_to_match.values())

            return reordered

        except Exception as e:
            logger.warning(f"LLM ranking failed: {e}")
            return matches

    def list_all(self) -> List[SSFDefinition]:
        """List all registered SSFs."""
        return list(self._ssfs.values())

    def list_by_risk(self, max_risk: RiskLevel) -> List[SSFDefinition]:
        """List SSFs up to a given risk level."""
        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        max_index = risk_order.index(max_risk)

        return [
            ssf for ssf in self._ssfs.values()
            if risk_order.index(ssf.risk_level) <= max_index
        ]

    def list_spawned_by(self, persona_id: UUID) -> List[SSFDefinition]:
        """List SSFs spawned by a persona."""
        ssf_ids = self._spawned_by_persona.get(persona_id, [])
        return [self._ssfs[id] for id in ssf_ids if id in self._ssfs]

    def get_pending_approvals(self) -> List[SSFDefinition]:
        """Get list of SSFs pending approval."""
        return list(self._pending_approvals.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        by_category = {}
        by_risk = {}

        for ssf in self._ssfs.values():
            cat = ssf.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            risk = ssf.risk_level.value
            by_risk[risk] = by_risk.get(risk, 0) + 1

        return {
            "total_ssfs": len(self._ssfs),
            "by_category": by_category,
            "by_risk": by_risk,
            "pending_approvals": len(self._pending_approvals),
            "total_spawned": sum(len(ids) for ids in self._spawned_by_persona.values()),
        }

    def reset_spawn_counts(self) -> None:
        """Reset session spawn counts (e.g., at session start)."""
        self._spawn_counts.clear()
