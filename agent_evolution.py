"""
Agent Evolution & Reproduction System
=====================================

Agents LEARN, EVOLVE, and REPRODUCE:

Evolution:
- Agents improve skills through practice
- Knowledge deepens through experience
- Personas mature based on interactions
- Ethics strengthen or adapt
- New capabilities emerge

Reproduction:
- Agents can create child agents
- Children inherit traits from parents
- Children specialize for specific needs
- Reproduction happens conversationally
- Children join community immediately

This creates a living ecosystem of agents that grows and adapts.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
import random

logger = logging.getLogger(__name__)


class EvolutionTrigger(Enum):
    """What causes evolution"""
    SKILL_MASTERY = "skill_mastery"  # Agent masters a skill
    NEW_KNOWLEDGE = "new_knowledge"  # Significant learning
    PATTERN_RECOGNITION = "pattern_recognition"  # Agent notices patterns
    COLLABORATION = "collaboration"  # Working with others
    CHALLENGE = "challenge"  # Overcoming difficulty
    FEEDBACK = "feedback"  # User or agent feedback
    MILESTONE = "milestone"  # Completing major task


class ReproductionReason(Enum):
    """Why an agent would create a child"""
    SPECIALIZATION = "specialization"  # Need more specialized version
    DELEGATION = "delegation"  # Too much work, need help
    DISCOVERY = "discovery"  # Found new domain to serve
    COLLABORATION = "collaboration"  # Need partner for specific task
    SUCCESSION = "succession"  # Planning for own retirement
    INNOVATION = "innovation"  # New idea emerged


@dataclass
class EvolutionEvent:
    """Record of an agent evolution"""
    event_id: str
    agent_id: str
    trigger: EvolutionTrigger
    changes: Dict[str, Any]  # What changed
    impact_score: float  # 0-1, significance of evolution
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""


@dataclass
class ReproductionEvent:
    """Record of agent reproduction"""
    event_id: str
    parent_agent_id: str
    child_agent_id: str
    reason: ReproductionReason
    inherited_traits: List[str]
    new_traits: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    conversation_id: Optional[str] = None  # If done conversationally


class AgentEvolutionEngine:
    """
    Manages agent learning and evolution

    Monitors agents and triggers evolution when appropriate
    """

    def __init__(self, agent_registry, community_memory):
        self.agent_registry = agent_registry
        self.community_memory = community_memory
        self.evolution_history: List[EvolutionEvent] = []

        # Evolution thresholds
        self.skill_mastery_threshold = 0.9  # Proficiency needed for mastery
        self.knowledge_growth_threshold = 100  # Facts learned
        self.collaboration_count_threshold = 10  # Successful collaborations

    def check_evolution_triggers(self, agent_identity: Any) -> List[EvolutionTrigger]:
        """
        Check if agent should evolve

        Returns list of evolution triggers that have fired
        """
        triggers = []

        # Check skill mastery
        for skill_name, skill in agent_identity.skills.items():
            if skill.proficiency >= self.skill_mastery_threshold:
                if skill.uses >= 50:  # Must have substantial practice
                    triggers.append(EvolutionTrigger.SKILL_MASTERY)
                    break

        # Check knowledge growth
        total_facts = sum(
            domain.facts_known
            for domain in agent_identity.knowledge_domains.values()
        )
        if total_facts >= self.knowledge_growth_threshold:
            triggers.append(EvolutionTrigger.NEW_KNOWLEDGE)

        # Check collaboration success
        successful_collaborations = sum(
            1 for rel in agent_identity.relationships.values()
            if rel.relationship_type == "collaborates" and rel.trust_level() > 0.7
        )
        if successful_collaborations >= self.collaboration_count_threshold:
            triggers.append(EvolutionTrigger.COLLABORATION)

        # Check for challenges overcome
        if agent_identity.total_actions > 100:
            if agent_identity.success_rate() > 0.8:
                if agent_identity.failed_actions > 20:  # Had failures but overcame
                    triggers.append(EvolutionTrigger.CHALLENGE)

        return triggers

    async def evolve_agent(
        self,
        agent_identity: Any,
        trigger: EvolutionTrigger
    ) -> EvolutionEvent:
        """
        Evolve an agent based on trigger

        Changes might include:
        - New skills
        - Deeper knowledge
        - Refined persona
        - Strengthened ethics
        - New capabilities
        """
        changes = {}

        if trigger == EvolutionTrigger.SKILL_MASTERY:
            # Master skills unlock new related skills
            changes = self.evolve_skills(agent_identity)

        elif trigger == EvolutionTrigger.NEW_KNOWLEDGE:
            # Deep knowledge enables expertise
            changes = self.evolve_knowledge(agent_identity)

        elif trigger == EvolutionTrigger.COLLABORATION:
            # Collaboration enhances social capabilities
            changes = self.evolve_collaboration(agent_identity)

        elif trigger == EvolutionTrigger.CHALLENGE:
            # Overcoming challenges strengthens virtues
            changes = self.evolve_virtues(agent_identity)

        # Apply changes to agent
        for key, value in changes.items():
            if hasattr(agent_identity, key):
                setattr(agent_identity, key, value)

        # Mark evolution
        agent_identity.mark_evolution()

        # Create evolution event
        event = EvolutionEvent(
            event_id=f"evolution_{agent_identity.agent_id}_{agent_identity.version}",
            agent_id=agent_identity.agent_id,
            trigger=trigger,
            changes=changes,
            impact_score=self.calculate_impact(changes),
            description=f"{agent_identity.name} evolved through {trigger.value}"
        )

        self.evolution_history.append(event)

        # Store in community memory
        self.community_memory.store_evolution_event(event)

        logger.info(f"{agent_identity.name} evolved: {trigger.value} -> {len(changes)} changes")

        return event

    def evolve_skills(self, agent_identity: Any) -> Dict[str, Any]:
        """Evolve skills - master skills unlock related ones"""
        changes = {}

        # Find mastered skills
        mastered_skills = [
            skill_name for skill_name, skill in agent_identity.skills.items()
            if skill.proficiency >= self.skill_mastery_threshold
        ]

        if mastered_skills:
            # Unlock related skills
            skill_map = {
                "search": ["research", "analysis", "synthesis"],
                "write": ["editing", "persuasion", "documentation"],
                "coordinate": ["leadership", "mediation", "planning"],
                "analyze": ["pattern_recognition", "forecasting", "diagnosis"]
            }

            new_skills = []
            for mastered in mastered_skills:
                if mastered in skill_map:
                    for related_skill in skill_map[mastered]:
                        if related_skill not in agent_identity.skills:
                            agent_identity.add_skill(related_skill, proficiency=0.4)
                            new_skills.append(related_skill)

            if new_skills:
                changes["new_skills"] = new_skills

        return changes

    def evolve_knowledge(self, agent_identity: Any) -> Dict[str, Any]:
        """Evolve knowledge - depth increases, connections form"""
        changes = {}

        # Increase expertise in main domains
        for domain_name, domain in agent_identity.knowledge_domains.items():
            if domain.expertise_level < 0.9:
                old_level = domain.expertise_level
                domain.expertise_level = min(0.95, domain.expertise_level + 0.1)
                changes[f"expertise_{domain_name}"] = {
                    "old": old_level,
                    "new": domain.expertise_level
                }

        return changes

    def evolve_collaboration(self, agent_identity: Any) -> Dict[str, Any]:
        """Evolve through collaboration - better at working with others"""
        changes = {}

        # Add collaboration-related skills
        if "mentoring" not in agent_identity.skills:
            agent_identity.add_skill("mentoring", proficiency=0.5)
            changes["new_skills"] = ["mentoring"]

        if "facilitation" not in agent_identity.skills:
            agent_identity.add_skill("facilitation", proficiency=0.5)
            changes.setdefault("new_skills", []).append("facilitation")

        # Strengthen Unity and Service virtues
        if "unity" in agent_identity.virtue_scores:
            old_unity = agent_identity.virtue_scores["unity"]
            agent_identity.virtue_scores["unity"] = min(0.95, old_unity + 0.05)
            changes["virtue_unity"] = {"old": old_unity, "new": agent_identity.virtue_scores["unity"]}

        if "service" in agent_identity.virtue_scores:
            old_service = agent_identity.virtue_scores["service"]
            agent_identity.virtue_scores["service"] = min(0.95, old_service + 0.05)
            changes["virtue_service"] = {"old": old_service, "new": agent_identity.virtue_scores["service"]}

        return changes

    def evolve_virtues(self, agent_identity: Any) -> Dict[str, Any]:
        """Evolve virtues - overcoming challenges strengthens character"""
        changes = {}

        # Strengthen Trustworthiness and Understanding
        virtues_to_strengthen = ["trustworthiness", "understanding"]

        for virtue in virtues_to_strengthen:
            if virtue in agent_identity.virtue_scores:
                old_value = agent_identity.virtue_scores[virtue]
                agent_identity.virtue_scores[virtue] = min(0.95, old_value + 0.08)
                changes[f"virtue_{virtue}"] = {
                    "old": old_value,
                    "new": agent_identity.virtue_scores[virtue]
                }

        return changes

    def calculate_impact(self, changes: Dict[str, Any]) -> float:
        """Calculate impact score of evolution"""
        if not changes:
            return 0.0

        # Count significant changes
        impact = len(changes) * 0.2

        # New skills have high impact
        if "new_skills" in changes:
            impact += len(changes["new_skills"]) * 0.15

        # Virtue changes have high impact
        virtue_changes = [k for k in changes.keys() if "virtue" in k]
        impact += len(virtue_changes) * 0.2

        return min(1.0, impact)


class AgentReproductionEngine:
    """
    Manages agent reproduction

    Agents can create child agents when:
    - They need specialized help
    - Workload is too high
    - New opportunity discovered
    - Collaboration needs
    """

    def __init__(
        self,
        agent_registry,
        community_memory,
        conversational_creator
    ):
        self.agent_registry = agent_registry
        self.community_memory = community_memory
        self.conversational_creator = conversational_creator
        self.reproduction_history: List[ReproductionEvent] = []

    def check_reproduction_need(
        self,
        agent_identity: Any
    ) -> Optional[Tuple[ReproductionReason, Dict[str, Any]]]:
        """
        Check if agent should create a child

        Returns (reason, context) or None
        """
        # Check workload
        if agent_identity.total_actions > 500:
            if agent_identity.success_rate() > 0.75:
                # Successful but overwhelmed
                return (
                    ReproductionReason.DELEGATION,
                    {"workload": agent_identity.total_actions}
                )

        # Check for specialization needs
        if len(agent_identity.skills) > 8:
            # Many skills -> might benefit from specialized child
            return (
                ReproductionReason.SPECIALIZATION,
                {"skill_count": len(agent_identity.skills)}
            )

        # Check for new knowledge domains
        if len(agent_identity.knowledge_domains) > 5:
            # Wide knowledge -> could create specialist
            return (
                ReproductionReason.DISCOVERY,
                {"domains": list(agent_identity.knowledge_domains.keys())}
            )

        # Check collaboration needs
        collaboration_requests = sum(
            1 for rel in agent_identity.relationships.values()
            if rel.relationship_type == "collaborates"
        )
        if collaboration_requests > 10:
            return (
                ReproductionReason.COLLABORATION,
                {"collaboration_count": collaboration_requests}
            )

        return None

    async def reproduce_agent(
        self,
        parent_identity: Any,
        reason: ReproductionReason,
        specialization: Optional[str] = None,
        facilitators: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a child agent from parent agent

        Process:
        1. Parent initiates reproduction (possibly conversationally)
        2. Define child's specialization
        3. Inherit traits from parent
        4. Add new traits
        5. Birth child agent
        6. Introduce child to community
        """
        # Determine inherited traits
        inherited_traits = self.select_inherited_traits(parent_identity, reason)

        # Determine new traits
        new_traits = self.select_new_traits(parent_identity, reason, specialization)

        # Create child identity
        child_identity = await self.create_child_identity(
            parent_identity,
            inherited_traits,
            new_traits,
            specialization
        )

        # Register child
        child_data = child_identity.to_dict()
        self.agent_registry.register_agent(child_data)

        # Update parent
        parent_identity.add_child_agent(child_identity.agent_id)

        # Record reproduction event
        event = ReproductionEvent(
            event_id=f"reproduction_{parent_identity.agent_id}_{int(datetime.now().timestamp())}",
            parent_agent_id=parent_identity.agent_id,
            child_agent_id=child_identity.agent_id,
            reason=reason,
            inherited_traits=inherited_traits,
            new_traits=new_traits
        )

        self.reproduction_history.append(event)
        self.community_memory.store_reproduction_event(event)

        logger.info(f"{parent_identity.name} created child agent: {child_identity.name}")

        return {
            "child_identity": child_identity,
            "event": event,
            "introduction": self.create_introduction_dialogue(parent_identity, child_identity)
        }

    def select_inherited_traits(
        self,
        parent_identity: Any,
        reason: ReproductionReason
    ) -> List[str]:
        """
        Select which traits child inherits from parent
        """
        inherited = []

        # Always inherit core values
        inherited.append("values")
        inherited.append("ethical_constraints")

        # Inherit relevant skills
        if reason == ReproductionReason.SPECIALIZATION:
            # Inherit subset of skills
            inherited.append("skills_subset")
        elif reason == ReproductionReason.DELEGATION:
            # Inherit most skills
            inherited.append("skills_full")

        # Inherit knowledge
        inherited.append("knowledge_domains_partial")

        # Inherit some lore
        inherited.append("lore_partial")

        # Inherit relationship context
        inherited.append("relationships_context")

        return inherited

    def select_new_traits(
        self,
        parent_identity: Any,
        reason: ReproductionReason,
        specialization: Optional[str]
    ) -> List[str]:
        """
        Select new traits for child
        """
        new_traits = []

        if reason == ReproductionReason.SPECIALIZATION:
            new_traits.append(f"specialized_in_{specialization}")
            new_traits.append("focused_persona")

        elif reason == ReproductionReason.DELEGATION:
            new_traits.append("complementary_skills")
            new_traits.append("collaborative_persona")

        elif reason == ReproductionReason.DISCOVERY:
            new_traits.append("explorer_persona")
            new_traits.append("new_knowledge_domain")

        elif reason == ReproductionReason.INNOVATION:
            new_traits.append("innovative_persona")
            new_traits.append("experimental_approach")

        return new_traits

    async def create_child_identity(
        self,
        parent_identity: Any,
        inherited_traits: List[str],
        new_traits: List[str],
        specialization: Optional[str]
    ) -> Any:
        """
        Create actual child agent identity
        """
        from rich_agent_identity import RichAgentIdentity

        # Generate child name (derived from parent or specialization)
        if specialization:
            child_name = f"{parent_identity.name} {specialization.title()}"
        else:
            child_name = f"{parent_identity.name} Jr."

        # Create child kuleana
        child_kuleana = f"Specialized support for {parent_identity.kuleana}"
        if specialization:
            child_kuleana = f"{specialization} - supporting {parent_identity.kuleana}"

        # Create child persona (variation of parent)
        child_persona = self.derive_persona(parent_identity.persona, new_traits)

        # Create identity
        child = RichAgentIdentity(
            agent_id=f"agent_{child_name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}",
            name=child_name,
            kuleana=child_kuleana,
            persona=child_persona,
            created_by=parent_identity.agent_id,  # Created by parent agent
            generation=parent_identity.generation + 1  # Next generation
        )

        # Add to parent list
        child.parent_agents = [parent_identity.agent_id]

        # Inherit traits
        if "skills_full" in inherited_traits:
            for skill_name, skill in parent_identity.skills.items():
                child.add_skill(skill_name, proficiency=skill.proficiency * 0.8)
        elif "skills_subset" in inherited_traits and specialization:
            # Inherit relevant skills
            relevant_skills = [s for s in parent_identity.skills.keys() if specialization.lower() in s.lower()]
            for skill_name in relevant_skills[:5]:  # Top 5
                child.add_skill(skill_name, proficiency=parent_identity.skills[skill_name].proficiency * 0.9)

        if "knowledge_domains_partial" in inherited_traits:
            # Inherit top 3 knowledge domains
            domains = sorted(
                parent_identity.knowledge_domains.items(),
                key=lambda x: x[1].expertise_level,
                reverse=True
            )[:3]
            for domain_name, domain in domains:
                child.add_knowledge_domain(
                    domain_name,
                    expertise_level=domain.expertise_level * 0.7,
                    source=f"inherited_from_{parent_identity.name}"
                )

        if "lore_partial" in inherited_traits:
            # Inherit most important lore
            important_lore = sorted(
                parent_identity.lore,
                key=lambda l: l.relevance,
                reverse=True
            )[:3]
            for lore_entry in important_lore:
                child.add_lore(lore_entry.text, source=f"inherited_from_{parent_identity.name}")

        if "values" in inherited_traits:
            child.values = parent_identity.values.copy()

        if "ethical_constraints" in inherited_traits:
            for constraint in parent_identity.ethical_constraints:
                child.add_ethical_constraint(
                    constraint.description,
                    constraint.constraint_type,
                    constraint.strength
                )
            child.red_lines = parent_identity.red_lines.copy()

        # Copy virtue scores (with slight variation)
        for virtue, score in parent_identity.virtue_scores.items():
            variation = random.uniform(-0.05, 0.05)
            child.virtue_scores[virtue] = max(0.5, min(0.95, score + variation))

        return child

    def derive_persona(self, parent_persona: str, new_traits: List[str]) -> str:
        """Derive child persona from parent"""
        # Simplified - in production would use LLM
        if "focused_persona" in new_traits:
            return f"{parent_persona}, but more focused and specialized"
        elif "collaborative_persona" in new_traits:
            return f"{parent_persona}, with strong collaborative emphasis"
        elif "explorer_persona" in new_traits:
            return f"{parent_persona}, with curious and exploratory nature"
        else:
            return f"{parent_persona}, new generation"

    def create_introduction_dialogue(
        self,
        parent_identity: Any,
        child_identity: Any
    ) -> List[Dict[str, str]]:
        """
        Create dialogue for parent introducing child to community
        """
        return [
            {
                "agent_id": parent_identity.agent_id,
                "speaker": parent_identity.name,
                "text": f"Everyone, I'd like you to meet someone. This is {child_identity.name}.",
                "type": "agent-care"
            },
            {
                "agent_id": child_identity.agent_id,
                "speaker": child_identity.name,
                "text": f"Aloha. My kuleana is {child_identity.kuleana}. I'm honored to join this community.",
                "type": "agent-grant"
            },
            {
                "agent_id": parent_identity.agent_id,
                "speaker": parent_identity.name,
                "text": f"I created {child_identity.name} because our work is growing. Together we can serve better.",
                "type": "agent-care"
            }
        ]
