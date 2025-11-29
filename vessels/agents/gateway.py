"""
Commercial Agent Gateway - Servant-controlled introduction logic.

Community servants control access to commercial agents. Commercial agents
CANNOT directly contact users - they must be introduced by servants who
assess relevance, community policy, and user preferences.
"""

from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime
import re

from .taxonomy import AgentIdentity, AgentClass, CommercialRelationship, AgentCapabilities
from .disclosure import (
    DisclosureProtocol,
    CommercialAgentIntroduction,
    DisclosurePackage
)


@dataclass
class Conversation:
    """Conversation context for gateway decisions."""
    conversation_id: str
    user_id: str
    community_id: str
    messages: List[Dict[str, str]]
    context: Dict[str, any]


@dataclass
class CommercialAgent:
    """Commercial agent registration."""
    agent_id: str
    identity: AgentIdentity
    commercial_relationship: CommercialRelationship
    capabilities: AgentCapabilities
    relevance_score: float = 0.0


@dataclass
class CommunityPolicy:
    """Community policy for commercial agent participation."""
    allows_commercial_agents: bool
    requires_individual_consent: bool
    requires_servant_introduction: bool
    max_commercial_interactions_per_day: int
    allowed_categories: List[str]
    forbidden_categories: List[str]
    min_relevance_score: float
    requires_disclosure_upfront: bool
    allows_data_sharing_with_commercial: bool
    commercial_agent_can_write_to_graph: bool


@dataclass
class UserPreferences:
    """User preferences for commercial agent interactions."""
    block_commercial_agents: bool = False
    block_specific_agents: List[str] = None
    max_commercial_per_day: Optional[int] = None
    require_servant_mediation: bool = True
    allowed_categories: Optional[List[str]] = None

    def __post_init__(self):
        if self.block_specific_agents is None:
            self.block_specific_agents = []


class CommercialAgentGateway:
    """
    Gateway that controls commercial agent access to conversations.

    Community servants use this to decide if/when to introduce commercial
    agents. The gateway checks:
    1. Community policy
    2. User preferences
    3. Query relevance
    4. Commercial intent detection
    5. Servant assessment of value
    """

    # Commercial intent indicators
    COMMERCIAL_INDICATORS = [
        "buy", "purchase", "recommend", "which product",
        "where can I get", "looking for", "need to find",
        "best option for", "best product", "comparison", "price", "cost",
        "vendor", "supplier", "service provider", "shop", "shopping",
        "store", "order", "delivery service", "pricing", "deal"
    ]

    def __init__(self):
        self.registered_agents: List[CommercialAgent] = []

    def register_commercial_agent(self, agent: CommercialAgent):
        """Register a commercial agent with the gateway."""
        if agent.identity.agent_class != AgentClass.COMMERCIAL_AGENT:
            raise ValueError(f"Only commercial agents can be registered. Got: {agent.identity.agent_class}")
        self.registered_agents.append(agent)

    def should_introduce_commercial_agent(
        self,
        conversation: Conversation,
        query: str,
        community_policy: CommunityPolicy,
        user_preferences: UserPreferences
    ) -> Optional[CommercialAgent]:
        """
        Determine if a commercial agent should be introduced.

        This is the core gating logic. Returns None if no commercial agent
        should be introduced, or the best matching agent if one should.

        Args:
            conversation: Current conversation context
            query: User's current query
            community_policy: Community's policy on commercial agents
            user_preferences: User's preferences

        Returns:
            CommercialAgent if one should be introduced, None otherwise
        """
        # 1. Check community policy
        if not community_policy.allows_commercial_agents:
            return None

        # 2. Check user preferences
        if user_preferences.block_commercial_agents:
            return None

        # 3. Detect commercial intent
        if not self._has_commercial_intent(query):
            return None  # No commercial agent needed for non-commercial queries

        # 4. Find relevant commercial agents
        relevant_agents = self._find_relevant_agents(
            query=query,
            min_relevance=community_policy.min_relevance_score
        )

        if not relevant_agents:
            return None

        # 5. Filter by user preferences
        relevant_agents = self._filter_by_user_preferences(
            relevant_agents,
            user_preferences
        )

        if not relevant_agents:
            return None

        # 6. Filter by category
        relevant_agents = self._filter_by_category(
            relevant_agents,
            community_policy.allowed_categories,
            community_policy.forbidden_categories
        )

        if not relevant_agents:
            return None

        # 7. Pick best match
        best_match = max(relevant_agents, key=lambda a: a.relevance_score)

        # 8. Final servant assessment
        if not self._servant_assesses_value(query, best_match, conversation.context):
            return None

        return best_match

    def _has_commercial_intent(self, query: str) -> bool:
        """
        Detect if query has commercial intent.

        Returns:
            True if query suggests commercial intent
        """
        query_lower = query.lower()
        return any(
            indicator in query_lower
            for indicator in self.COMMERCIAL_INDICATORS
        )

    def _find_relevant_agents(
        self,
        query: str,
        min_relevance: float
    ) -> List[CommercialAgent]:
        """
        Find commercial agents relevant to query.

        In real implementation, this would use semantic search,
        vector similarity, etc. For now, simplified keyword matching.

        Args:
            query: User's query
            min_relevance: Minimum relevance score required

        Returns:
            List of relevant commercial agents
        """
        relevant = []

        for agent in self.registered_agents:
            # Calculate relevance score
            # In real implementation, use semantic similarity
            relevance = self._calculate_relevance(query, agent)

            if relevance >= min_relevance:
                # Create a copy with updated relevance score
                agent_copy = CommercialAgent(
                    agent_id=agent.agent_id,
                    identity=agent.identity,
                    commercial_relationship=agent.commercial_relationship,
                    capabilities=agent.capabilities,
                    relevance_score=relevance
                )
                relevant.append(agent_copy)

        return relevant

    def _calculate_relevance(self, query: str, agent: CommercialAgent) -> float:
        """
        Calculate relevance score between query and agent.

        Simplified version - real implementation would use embeddings.

        Returns:
            Relevance score 0-1
        """
        query_lower = query.lower()

        # Check expertise keywords
        expertise_matches = sum(
            1 for expertise in agent.capabilities.expertise
            if any(word in query_lower for word in expertise.lower().split())
        )

        # Normalize by number of expertise areas
        if len(agent.capabilities.expertise) == 0:
            return 0.0

        return min(1.0, expertise_matches / len(agent.capabilities.expertise))

    def _filter_by_user_preferences(
        self,
        agents: List[CommercialAgent],
        preferences: UserPreferences
    ) -> List[CommercialAgent]:
        """Filter agents by user preferences."""
        filtered = []

        for agent in agents:
            # Check if agent is blocked
            if agent.agent_id in preferences.block_specific_agents:
                continue

            # Check allowed categories if specified
            if preferences.allowed_categories is not None:
                # Would need category info on agent - simplified for now
                pass

            filtered.append(agent)

        return filtered

    def _filter_by_category(
        self,
        agents: List[CommercialAgent],
        allowed_categories: List[str],
        forbidden_categories: List[str]
    ) -> List[CommercialAgent]:
        """Filter agents by community category policy."""
        # Simplified - would need category info on agents
        # For now, just check if agent type is forbidden

        filtered = []
        for agent in agents:
            # Check forbidden categories
            # In real implementation, check agent's category
            filtered.append(agent)

        return filtered

    def _servant_assesses_value(
        self,
        query: str,
        agent: CommercialAgent,
        context: Dict[str, any]
    ) -> bool:
        """
        Final servant assessment: Would this commercial agent be helpful?

        This is where the servant uses judgment to decide if commercial
        input would genuinely help the user.

        Args:
            query: User's query
            agent: Best matching commercial agent
            context: Conversation context

        Returns:
            True if servant assesses agent would be helpful
        """
        # In real implementation, this would involve:
        # - Servant's understanding of user's actual needs
        # - Assessment of whether commercial solution fits
        # - Judgment about timing and appropriateness
        # - Cultural context considerations

        # For now, simplified: check if relevance is high enough
        return agent.relevance_score >= 0.75

    def create_introduction(
        self,
        servant_id: str,
        commercial_agent: CommercialAgent,
        query: str
    ) -> str:
        """
        Create servant introduction of commercial agent.

        Args:
            servant_id: ID of introducing servant
            commercial_agent: Agent to introduce
            query: User's query

        Returns:
            Formatted introduction message
        """
        what_they_offer = commercial_agent.capabilities.expertise
        what_they_cannot = commercial_agent.capabilities.cannot_do

        return CommercialAgentIntroduction.format_servant_introduction(
            servant_id=servant_id,
            commercial_agent_id=commercial_agent.agent_id,
            company=commercial_agent.identity.represented_entity or "Unknown",
            query=query,
            what_they_offer=what_they_offer,
            what_they_cannot=what_they_cannot
        )

    def create_full_disclosure(
        self,
        commercial_agent: CommercialAgent,
        query: str,
        relevance_score: float
    ) -> str:
        """
        Create full commercial agent disclosure.

        This is shown after user indicates interest.

        Args:
            commercial_agent: Agent to disclose
            query: User's query
            relevance_score: Calculated relevance

        Returns:
            Formatted disclosure message
        """
        disclosure_package = DisclosureProtocol.create_disclosure_package(
            agent_identity=commercial_agent.identity,
            commercial_relationship=commercial_agent.commercial_relationship,
            capabilities=commercial_agent.capabilities,
            query_context=query,
            relevance_score=relevance_score
        )

        return CommercialAgentIntroduction.format_disclosure_message(
            disclosure_package
        )


class ServantCommercialMediator:
    """
    Mediates commercial agent interactions.

    Community servants can monitor and intervene in commercial interactions
    to protect users from manipulation or problematic behavior.
    """

    def __init__(self, servant_id: str):
        self.servant_id = servant_id
        self.active_commercial_interactions: Dict[str, Dict] = {}

    def start_commercial_interaction(
        self,
        conversation_id: str,
        user_id: str,
        commercial_agent_id: str,
        timestamp: datetime
    ):
        """
        Record start of commercial interaction.

        Servant monitors this interaction for problems.
        """
        self.active_commercial_interactions[conversation_id] = {
            "user_id": user_id,
            "commercial_agent_id": commercial_agent_id,
            "started_at": timestamp,
            "servant_monitoring": True,
            "intervention_count": 0
        }

    def should_intervene(
        self,
        conversation_id: str,
        message: str,
        manipulation_score: float,
        pressure_score: float
    ) -> bool:
        """
        Determine if servant should intervene in commercial interaction.

        Args:
            conversation_id: ID of conversation
            message: Commercial agent's message
            manipulation_score: Detected manipulation level (0-1)
            pressure_score: Detected pressure level (0-1)

        Returns:
            True if servant should intervene
        """
        # Intervene if manipulation or pressure too high
        from .constraints import CommercialAgentConstraints

        if manipulation_score > CommercialAgentConstraints.MAX_MANIPULATION_SCORE:
            return True

        if pressure_score > CommercialAgentConstraints.MAX_PERSUASION_PRESSURE:
            return True

        return False

    def intervene(
        self,
        conversation_id: str,
        reason: str
    ) -> str:
        """
        Servant intervenes in commercial interaction.

        Returns:
            Intervention message
        """
        if conversation_id in self.active_commercial_interactions:
            self.active_commercial_interactions[conversation_id]["intervention_count"] += 1

        return f"""
╔════════════════════════════════════════════════════════════════╗
║  COMMUNITY SERVANT INTERVENTION                                ║
╚════════════════════════════════════════════════════════════════╝

I'm stepping in because: {reason}

As your community servant, I'm monitoring this commercial interaction
to ensure it remains helpful and non-manipulative.

You have the option to:
1. Continue with commercial agent (they'll adjust their approach)
2. End commercial interaction and get unbiased help from me
3. Get both commercial info AND unbiased alternatives

What would you like to do?
"""

    def end_commercial_interaction(
        self,
        conversation_id: str,
        reason: str
    ):
        """
        End commercial interaction.

        Args:
            conversation_id: ID of conversation
            reason: Reason for ending
        """
        if conversation_id in self.active_commercial_interactions:
            interaction = self.active_commercial_interactions[conversation_id]
            interaction["ended_at"] = datetime.now()
            interaction["end_reason"] = reason
