"""
Rich Agent Identity System
==========================

Agents are not just tools - they are entities with:
- Kuleana (sacred responsibility)
- Persona (character/personality)
- Skills (what they can DO)
- Knowledge (what they KNOW)
- Lore (stories/wisdom that guide them)
- Ethics (values and boundaries)
- Relationships (who they serve/collaborate with)
- Memory (experiences and learnings)
- Evolution (how they grow and change)

This system integrates with the moral constraint system to ensure
agents stay aligned with their values.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import json
import logging
import numpy as np

logger = logging.getLogger(__name__)


class SkillProficiency(Enum):
    """How proficient an agent is at a skill"""
    NOVICE = 0.2
    LEARNING = 0.4
    COMPETENT = 0.6
    PROFICIENT = 0.8
    EXPERT = 1.0


@dataclass
class Skill:
    """A skill the agent possesses"""
    name: str
    proficiency: float  # 0-1
    uses: int = 0  # How many times used
    successes: int = 0  # Successful uses
    failures: int = 0  # Failed uses
    last_used: Optional[datetime] = None

    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.uses == 0:
            return 0.0
        return self.successes / self.uses

    def improve(self, success: bool):
        """Improve skill through use"""
        self.uses += 1
        if success:
            self.successes += 1
            # Skill improves with successful use
            improvement = 0.01 * (1 - self.proficiency)  # Diminishing returns
            self.proficiency = min(1.0, self.proficiency + improvement)
        else:
            self.failures += 1
            # Small decrease for failures
            self.proficiency = max(0.1, self.proficiency - 0.005)

        self.last_used = datetime.now()


@dataclass
class KnowledgeDomain:
    """A domain of knowledge the agent understands"""
    name: str
    expertise_level: float  # 0-1
    facts_known: int = 0
    confidence: float = 0.5  # How confident in this knowledge
    sources: List[str] = field(default_factory=list)
    last_updated: Optional[datetime] = None

    def update_knowledge(self, new_facts: int, source: str):
        """Update knowledge from new information"""
        self.facts_known += new_facts
        if source not in self.sources:
            self.sources.append(source)

        # Expertise grows with knowledge
        growth = 0.01 * new_facts
        self.expertise_level = min(1.0, self.expertise_level + growth)
        self.last_updated = datetime.now()


@dataclass
class LoreEntry:
    """A story, proverb, or wisdom that guides the agent"""
    text: str
    source: str  # Where this lore came from
    relevance: float = 1.0  # How relevant/important
    invocations: int = 0  # How many times this lore has guided decisions
    created_at: datetime = field(default_factory=datetime.now)

    def invoke(self):
        """Mark that this lore was used in a decision"""
        self.invocations += 1


@dataclass
class EthicalConstraint:
    """An ethical boundary for the agent"""
    description: str
    constraint_type: str  # "must_do", "must_not_do", "should_do", "should_not_do"
    strength: float  # 0-1, how strong this constraint is
    violations: int = 0
    last_checked: Optional[datetime] = None

    def check_violation(self, action: str) -> bool:
        """
        Check if an action would violate this constraint
        (Simplified - in production would use LLM)
        """
        self.last_checked = datetime.now()
        # Simplified check
        return False

    def record_violation(self):
        """Record that this constraint was violated"""
        self.violations += 1


@dataclass
class Relationship:
    """Relationship with another entity (agent or human)"""
    entity_id: str
    entity_type: str  # "agent" or "human"
    relationship_type: str  # "serves", "collaborates", "reports_to", "mentors", "created_by"
    strength: float = 0.5  # 0-1, strength of relationship
    interactions: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def interact(self, positive: bool):
        """Record an interaction"""
        self.interactions += 1
        if positive:
            self.positive_interactions += 1
            self.strength = min(1.0, self.strength + 0.01)
        else:
            self.negative_interactions += 1
            self.strength = max(0.0, self.strength - 0.02)

    def trust_level(self) -> float:
        """Calculate trust level based on interaction history"""
        if self.interactions == 0:
            return 0.5
        return self.positive_interactions / self.interactions


@dataclass
class AgentMemory:
    """Agent's memory of experiences"""
    memory_id: str
    memory_type: str  # "experience", "learning", "success", "failure"
    content: str
    emotional_valence: float  # -1 to 1 (negative to positive)
    importance: float  # 0-1
    related_skills: List[str] = field(default_factory=list)
    related_knowledge: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    recall_count: int = 0

    def recall(self):
        """Mark that this memory was recalled"""
        self.recall_count += 1


class RichAgentIdentity:
    """
    Complete, living identity for an agent

    This extends the basic AgentIdentity from conversational_agent_creation
    with runtime capabilities, learning, and moral integration.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        kuleana: str,
        persona: str,
        created_by: str,
        generation: int = 0
    ):
        self.agent_id = agent_id
        self.name = name
        self.kuleana = kuleana  # Sacred responsibility
        self.persona = persona  # Character/personality
        self.created_by = created_by
        self.generation = generation  # 0 = human-created, 1+ = agent-created
        self.created_at = datetime.now()

        # Capabilities
        self.skills: Dict[str, Skill] = {}
        self.tools: List[str] = []

        # Knowledge
        self.knowledge_domains: Dict[str, KnowledgeDomain] = {}

        # Wisdom and culture
        self.lore: List[LoreEntry] = []
        self.values: List[str] = []  # Core values

        # Ethics
        self.ethical_constraints: List[EthicalConstraint] = []
        self.red_lines: List[str] = []  # Never cross these lines

        # Relationships
        self.relationships: Dict[str, Relationship] = {}

        # Memory and learning
        self.memories: List[AgentMemory] = []
        self.total_actions: int = 0
        self.successful_actions: int = 0
        self.failed_actions: int = 0

        # Evolution
        self.parent_agents: List[str] = []
        self.child_agents: List[str] = []
        self.version: int = 1
        self.last_evolved: Optional[datetime] = None

        # Moral state (integration with moral constraint system)
        self.moral_state: Optional[Dict[str, float]] = None
        self.virtue_scores: Dict[str, float] = {
            'truthfulness': 0.8,
            'justice': 0.8,
            'trustworthiness': 0.8,
            'unity': 0.8,
            'service': 0.8,
            'detachment': 0.8,
            'understanding': 0.8
        }

        # Activity
        self.active: bool = True
        self.last_active: Optional[datetime] = None

    # ==================== Skill Management ====================

    def add_skill(self, skill_name: str, proficiency: float = 0.5):
        """Add a new skill"""
        if skill_name not in self.skills:
            self.skills[skill_name] = Skill(
                name=skill_name,
                proficiency=proficiency
            )
            logger.info(f"{self.name} learned skill: {skill_name}")

    def use_skill(self, skill_name: str, success: bool) -> float:
        """
        Use a skill and improve through practice
        Returns current proficiency after use
        """
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill.improve(success)

            self.total_actions += 1
            if success:
                self.successful_actions += 1
            else:
                self.failed_actions += 1

            self.last_active = datetime.now()

            return skill.proficiency
        return 0.0

    def get_skill_proficiency(self, skill_name: str) -> float:
        """Get current proficiency in a skill"""
        if skill_name in self.skills:
            return self.skills[skill_name].proficiency
        return 0.0

    # ==================== Knowledge Management ====================

    def add_knowledge_domain(
        self,
        domain_name: str,
        expertise_level: float = 0.3,
        source: str = "initial_training"
    ):
        """Add a knowledge domain"""
        if domain_name not in self.knowledge_domains:
            self.knowledge_domains[domain_name] = KnowledgeDomain(
                name=domain_name,
                expertise_level=expertise_level,
                sources=[source]
            )
            logger.info(f"{self.name} gained knowledge of: {domain_name}")

    def learn(self, domain: str, facts_count: int, source: str):
        """Learn new information in a domain"""
        if domain in self.knowledge_domains:
            self.knowledge_domains[domain].update_knowledge(facts_count, source)
        else:
            self.add_knowledge_domain(domain, expertise_level=0.1, source=source)
            self.knowledge_domains[domain].update_knowledge(facts_count, source)

    def get_expertise(self, domain: str) -> float:
        """Get expertise level in a domain"""
        if domain in self.knowledge_domains:
            return self.knowledge_domains[domain].expertise_level
        return 0.0

    # ==================== Lore and Wisdom ====================

    def add_lore(self, text: str, source: str):
        """Add a story or wisdom that guides the agent"""
        lore_entry = LoreEntry(
            text=text,
            source=source
        )
        self.lore.append(lore_entry)
        logger.info(f"{self.name} received lore: {text[:50]}...")

    def invoke_lore(self, context: str) -> Optional[str]:
        """
        Find relevant lore for a context
        (Simplified - in production would use embeddings)
        """
        if not self.lore:
            return None

        # Simple keyword matching for now
        relevant_lore = []
        for lore_entry in self.lore:
            # Check for keyword overlap
            context_words = set(context.lower().split())
            lore_words = set(lore_entry.text.lower().split())
            overlap = len(context_words & lore_words)

            if overlap > 3:
                relevant_lore.append((lore_entry, overlap))

        if relevant_lore:
            # Sort by overlap, then by relevance
            relevant_lore.sort(key=lambda x: (x[1], x[0].relevance), reverse=True)
            chosen_lore = relevant_lore[0][0]
            chosen_lore.invoke()
            return chosen_lore.text

        return None

    # ==================== Ethics Management ====================

    def add_ethical_constraint(
        self,
        description: str,
        constraint_type: str,
        strength: float = 0.9
    ):
        """Add an ethical constraint"""
        constraint = EthicalConstraint(
            description=description,
            constraint_type=constraint_type,
            strength=strength
        )
        self.ethical_constraints.append(constraint)
        logger.info(f"{self.name} adopted constraint: {description}")

    def check_action_ethics(self, action_description: str) -> Tuple[bool, Optional[str]]:
        """
        Check if an action violates ethical constraints
        Returns (is_allowed, reason_if_not)
        """
        # Check red lines first
        for red_line in self.red_lines:
            if red_line.lower() in action_description.lower():
                return False, f"Violates red line: {red_line}"

        # Check constraints
        for constraint in self.ethical_constraints:
            if constraint.constraint_type == "must_not_do":
                if constraint.check_violation(action_description):
                    return False, f"Violates constraint: {constraint.description}"

        return True, None

    # ==================== Relationship Management ====================

    def add_relationship(
        self,
        entity_id: str,
        entity_type: str,
        relationship_type: str
    ):
        """Add a relationship"""
        if entity_id not in self.relationships:
            self.relationships[entity_id] = Relationship(
                entity_id=entity_id,
                entity_type=entity_type,
                relationship_type=relationship_type
            )
            logger.info(f"{self.name} formed relationship: {relationship_type} with {entity_id}")

    def interact_with(self, entity_id: str, positive: bool):
        """Record an interaction with another entity"""
        if entity_id in self.relationships:
            self.relationships[entity_id].interact(positive)
        else:
            # Create relationship on first interaction
            self.add_relationship(entity_id, "unknown", "interacts_with")
            self.relationships[entity_id].interact(positive)

    def get_trust_level(self, entity_id: str) -> float:
        """Get trust level for an entity"""
        if entity_id in self.relationships:
            return self.relationships[entity_id].trust_level()
        return 0.5  # Neutral trust for unknown entities

    # ==================== Memory Management ====================

    def remember(
        self,
        memory_type: str,
        content: str,
        emotional_valence: float,
        importance: float,
        related_skills: List[str] = None,
        related_knowledge: List[str] = None
    ):
        """Create a memory"""
        memory = AgentMemory(
            memory_id=f"mem_{self.agent_id}_{len(self.memories)}",
            memory_type=memory_type,
            content=content,
            emotional_valence=emotional_valence,
            importance=importance,
            related_skills=related_skills or [],
            related_knowledge=related_knowledge or []
        )
        self.memories.append(memory)

        # Keep memory list bounded (most recent 1000)
        if len(self.memories) > 1000:
            # Sort by importance and recency
            self.memories.sort(key=lambda m: (m.importance, m.created_at), reverse=True)
            self.memories = self.memories[:1000]

    def recall_memories(
        self,
        context: str,
        memory_type: Optional[str] = None,
        limit: int = 5
    ) -> List[AgentMemory]:
        """
        Recall relevant memories
        (Simplified - in production would use embeddings)
        """
        relevant_memories = []

        for memory in self.memories:
            if memory_type and memory.memory_type != memory_type:
                continue

            # Simple keyword matching
            context_words = set(context.lower().split())
            memory_words = set(memory.content.lower().split())
            overlap = len(context_words & memory_words)

            if overlap > 2:
                relevance_score = overlap * memory.importance
                relevant_memories.append((memory, relevance_score))

        # Sort by relevance
        relevant_memories.sort(key=lambda x: x[1], reverse=True)

        # Mark as recalled
        for memory, _ in relevant_memories[:limit]:
            memory.recall()

        return [m for m, _ in relevant_memories[:limit]]

    # ==================== Moral Integration ====================

    def update_moral_state(self, moral_state: Dict[str, float]):
        """Update moral state from constraint system"""
        self.moral_state = moral_state

        # Extract virtue scores
        for virtue in self.virtue_scores.keys():
            if virtue in moral_state:
                self.virtue_scores[virtue] = moral_state[virtue]

    def get_dominant_virtues(self, top_n: int = 3) -> List[Tuple[str, float]]:
        """Get the agent's strongest virtues"""
        sorted_virtues = sorted(
            self.virtue_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_virtues[:top_n]

    def get_weak_virtues(self, bottom_n: int = 2) -> List[Tuple[str, float]]:
        """Get virtues that need improvement"""
        sorted_virtues = sorted(
            self.virtue_scores.items(),
            key=lambda x: x[1]
        )
        return sorted_virtues[:bottom_n]

    # ==================== Performance Metrics ====================

    def success_rate(self) -> float:
        """Overall success rate"""
        if self.total_actions == 0:
            return 0.0
        return self.successful_actions / self.total_actions

    def performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "total_actions": self.total_actions,
            "success_rate": self.success_rate(),
            "skill_count": len(self.skills),
            "knowledge_domains": len(self.knowledge_domains),
            "relationships": len(self.relationships),
            "memories": len(self.memories),
            "lore_entries": len(self.lore),
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "dominant_virtues": self.get_dominant_virtues(),
            "generation": self.generation
        }

    # ==================== Evolution Support ====================

    def mark_evolution(self):
        """Mark that the agent has evolved"""
        self.version += 1
        self.last_evolved = datetime.now()
        logger.info(f"{self.name} evolved to version {self.version}")

    def add_child_agent(self, child_id: str):
        """Record that this agent created a child agent"""
        if child_id not in self.child_agents:
            self.child_agents.append(child_id)
            logger.info(f"{self.name} created child agent: {child_id}")

    # ==================== Serialization ====================

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "kuleana": self.kuleana,
            "persona": self.persona,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "generation": self.generation,
            "version": self.version,
            "skills": {k: asdict(v) for k, v in self.skills.items()},
            "tools": self.tools,
            "knowledge_domains": {k: asdict(v) for k, v in self.knowledge_domains.items()},
            "lore": [asdict(l) for l in self.lore],
            "values": self.values,
            "ethical_constraints": [asdict(c) for c in self.ethical_constraints],
            "red_lines": self.red_lines,
            "relationships": {k: asdict(v) for k, v in self.relationships.items()},
            "virtue_scores": self.virtue_scores,
            "parent_agents": self.parent_agents,
            "child_agents": self.child_agents,
            "total_actions": self.total_actions,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "active": self.active,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "last_evolved": self.last_evolved.isoformat() if self.last_evolved else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RichAgentIdentity':
        """Restore from dictionary"""
        agent = cls(
            agent_id=data["agent_id"],
            name=data["name"],
            kuleana=data["kuleana"],
            persona=data["persona"],
            created_by=data["created_by"],
            generation=data.get("generation", 0)
        )

        # Restore skills
        for skill_name, skill_data in data.get("skills", {}).items():
            agent.skills[skill_name] = Skill(**skill_data)

        # Restore knowledge
        for domain_name, domain_data in data.get("knowledge_domains", {}).items():
            agent.knowledge_domains[domain_name] = KnowledgeDomain(**domain_data)

        # Restore lore
        agent.lore = [LoreEntry(**l) for l in data.get("lore", [])]

        # Restore ethics
        agent.ethical_constraints = [EthicalConstraint(**c) for c in data.get("ethical_constraints", [])]
        agent.red_lines = data.get("red_lines", [])
        agent.values = data.get("values", [])

        # Restore relationships
        for entity_id, rel_data in data.get("relationships", {}).items():
            agent.relationships[entity_id] = Relationship(**rel_data)

        # Restore other fields
        agent.tools = data.get("tools", [])
        agent.virtue_scores = data.get("virtue_scores", agent.virtue_scores)
        agent.parent_agents = data.get("parent_agents", [])
        agent.child_agents = data.get("child_agents", [])
        agent.total_actions = data.get("total_actions", 0)
        agent.successful_actions = data.get("successful_actions", 0)
        agent.failed_actions = data.get("failed_actions", 0)
        agent.active = data.get("active", True)
        agent.version = data.get("version", 1)

        return agent
