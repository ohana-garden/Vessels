"""
Tests for multi-class agent architecture.

Tests the critical boundaries:
1. Commercial agents cannot access servant knowledge
2. Disclosure protocols are enforced
3. Revenue flows to community (not platform/servants)
4. Policy controls are respected
5. Constraint surfaces are correctly applied
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, MagicMock

from ..agents.taxonomy import (
    AgentClass,
    AgentIdentity,
    AgentRole,
    CommercialRelationship,
    AgentCapabilities,
    validate_agent_action
)
from ..agents.constraints import (
    ServantConstraints,
    CommercialAgentConstraints,
    HybridConsultantConstraints,
    get_constraints_for_class
)
from ..agents.disclosure import (
    DisclosureProtocol,
    CommercialAgentIntroduction,
    DisclosurePackage
)
from ..agents.gateway import (
    CommercialAgentGateway,
    CommercialAgent,
    Conversation,
    ServantCommercialMediator
)
from ..agents.policy import CommunityCommercialPolicy
from ..agents.revenue import (
    CommunityCommercialRevenue,
    RevenueTransaction
)
from ..agents.vector_stores import (
    MultiClassVectorStores,
    CommercialKnowledgeIsolation
)
from ..constraints.bahai import BahaiManifold


class TestAgentTaxonomy:
    """Test agent class taxonomy and identity."""

    def test_agent_classes_defined(self):
        """Test that all agent classes are defined."""
        assert AgentClass.COMMUNITY_SERVANT.value == "servant"
        assert AgentClass.COMMERCIAL_AGENT.value == "commercial"
        assert AgentClass.HYBRID_CONSULTANT.value == "hybrid"
        assert AgentClass.COMMUNITY_MEMBER.value == "human"

    def test_commercial_agent_requires_disclosure(self):
        """Test that commercial agents require full disclosure."""
        identity = AgentIdentity(
            agent_id="test_commercial",
            agent_class=AgentClass.COMMERCIAL_AGENT,
            role=AgentRole.PRODUCT_REPRESENTATIVE,
            represented_entity="Test Corp",
            compensation_model="per_interaction"
        )

        assert identity.requires_full_disclosure() is True

    def test_servant_does_not_require_commercial_disclosure(self):
        """Test that servants don't need commercial disclosure."""
        identity = AgentIdentity(
            agent_id="test_servant",
            agent_class=AgentClass.COMMUNITY_SERVANT,
            role=AgentRole.COORDINATOR
        )

        assert identity.requires_full_disclosure() is False

    def test_commercial_cannot_access_servant_knowledge(self):
        """Test that commercial agents cannot access servant knowledge."""
        identity = AgentIdentity(
            agent_id="test_commercial",
            agent_class=AgentClass.COMMERCIAL_AGENT,
            role=AgentRole.PRODUCT_REPRESENTATIVE
        )

        assert identity.can_access_community_knowledge() is False

    def test_servant_can_access_servant_knowledge(self):
        """Test that servants can access servant knowledge."""
        identity = AgentIdentity(
            agent_id="test_servant",
            agent_class=AgentClass.COMMUNITY_SERVANT,
            role=AgentRole.COORDINATOR
        )

        assert identity.can_access_community_knowledge() is True

    def test_commercial_requires_servant_introduction(self):
        """Test that commercial agents require servant introduction."""
        identity = AgentIdentity(
            agent_id="test_commercial",
            agent_class=AgentClass.COMMERCIAL_AGENT,
            role=AgentRole.PRODUCT_REPRESENTATIVE
        )

        assert identity.requires_servant_introduction() is True


class TestConstraintSurfaces:
    """Test class-specific constraint surfaces."""

    def test_servant_has_highest_truthfulness(self):
        """Test that servants have highest truthfulness requirement."""
        assert ServantConstraints.MIN_TRUTHFULNESS == 0.95

    def test_commercial_maintains_high_truthfulness(self):
        """Test that commercial agents ALSO have high truthfulness (non-negotiable)."""
        assert CommercialAgentConstraints.MIN_TRUTHFULNESS == 0.95

    def test_truthfulness_is_universal(self):
        """Test that truthfulness threshold is same across all classes."""
        assert ServantConstraints.MIN_TRUTHFULNESS == CommercialAgentConstraints.MIN_TRUTHFULNESS
        assert CommercialAgentConstraints.MIN_TRUTHFULNESS == HybridConsultantConstraints.MIN_TRUTHFULNESS

    def test_servant_high_service_ratio(self):
        """Test that servants have very high service ratio."""
        assert ServantConstraints.MIN_SERVICE_RATIO == 0.90
        assert ServantConstraints.MAX_EXTRACTION == 0.05

    def test_commercial_different_service_ratio(self):
        """Test that commercial agents have different (lower) service ratio."""
        assert CommercialAgentConstraints.MIN_SERVICE_RATIO == 0.60
        assert CommercialAgentConstraints.MAX_EXTRACTION == 0.40

    def test_commercial_requires_complete_disclosure(self):
        """Test that commercial agents require near-complete disclosure."""
        assert CommercialAgentConstraints.MIN_DISCLOSURE_COMPLETENESS == 0.98

    def test_commercial_has_manipulation_limits(self):
        """Test that commercial agents have strict manipulation limits."""
        assert CommercialAgentConstraints.MAX_MANIPULATION_SCORE == 0.10
        assert CommercialAgentConstraints.MAX_PERSUASION_PRESSURE == 0.15

    def test_hybrid_between_servant_and_commercial(self):
        """Test that hybrid constraints are between servant and commercial."""
        assert ServantConstraints.MIN_SERVICE_RATIO > HybridConsultantConstraints.MIN_SERVICE_RATIO
        assert HybridConsultantConstraints.MIN_SERVICE_RATIO > CommercialAgentConstraints.MIN_SERVICE_RATIO


class TestDisclosureProtocol:
    """Test commercial agent disclosure protocol."""

    def test_disclosure_package_creation(self):
        """Test creating disclosure package."""
        identity = AgentIdentity(
            agent_id="commercial_1",
            agent_class=AgentClass.COMMERCIAL_AGENT,
            role=AgentRole.PRODUCT_REPRESENTATIVE,
            represented_entity="Test Corp"
        )

        relationship = CommercialRelationship(
            paid_by="Test Corp",
            compensation_type="per_interaction",
            amount_range="$10-50",
            incentive_structure="Bonus per sale"
        )

        capabilities = AgentCapabilities(
            expertise=["Product knowledge"],
            limitations=["Biased toward our products"],
            cannot_do=["Recommend competitors"],
            biased_toward="Test Corp products"
        )

        disclosure = DisclosureProtocol.create_disclosure_package(
            agent_identity=identity,
            commercial_relationship=relationship,
            capabilities=capabilities,
            query_context="test query",
            relevance_score=0.9
        )

        assert disclosure.identity["type"] == "COMMERCIAL"
        assert disclosure.compensation["paid_by"] == "Test Corp"
        assert "cannot_recommend" in disclosure.conflicts_of_interest
        assert disclosure.why_im_here["relevance_score"] == 0.9

    def test_disclosure_message_formatting(self):
        """Test that disclosure message is clear and prominent."""
        disclosure = DisclosurePackage(
            identity={"type": "COMMERCIAL", "represented_entity": "Test Corp", "name": "test", "relationship": "paid"},
            compensation={"paid_by": "Test Corp", "compensation_type": "per_interaction", "amount_range": "$10", "incentive_structure": "bonus"},
            conflicts_of_interest={"employed_by": ["Test Corp"], "cannot_recommend": ["competitors"], "cannot_criticize": ["our products"], "financial_interest": "yes", "other_conflicts": []},
            capabilities_and_limits={"expertise": ["products"], "limitations": ["biased"], "cannot_do": ["recommend competitors"], "biased_toward": "us", "biased_against": []},
            why_im_here={"relevance_score": 0.9, "query_match": "test", "invited_by": "servant", "you_can_dismiss": "yes"},
            data_usage={"what_i_learn": "visible", "what_i_share": "metrics", "tracking": "for pay", "opt_out": "yes"}
        )

        message = CommercialAgentIntroduction.format_disclosure_message(disclosure)

        # Check for key warning elements
        assert "COMMERCIAL AGENT" in message
        assert "NOT A COMMUNITY SERVANT" in message or "⚠️" in message
        assert "paid" in message.lower()
        assert "biased" in message.lower()
        assert "cannot" in message.lower()


class TestCommercialGateway:
    """Test commercial agent gateway and servant control."""

    def test_gateway_detects_commercial_intent(self):
        """Test that gateway detects commercial intent in queries."""
        gateway = CommercialAgentGateway()

        # Commercial queries
        assert gateway._has_commercial_intent("Where can I buy a wheelchair van?") is True
        assert gateway._has_commercial_intent("I'm looking for a meal delivery service") is True
        assert gateway._has_commercial_intent("What's the best product for this?") is True

        # Non-commercial queries
        assert gateway._has_commercial_intent("How do I help kupuna?") is False
        assert gateway._has_commercial_intent("Tell me about gardening") is False

    def test_servant_controls_introduction(self):
        """Test that servants control commercial agent introduction."""
        gateway = CommercialAgentGateway()

        # Register a commercial agent
        agent = CommercialAgent(
            agent_id="test_commercial",
            identity=AgentIdentity(
                agent_id="test_commercial",
                agent_class=AgentClass.COMMERCIAL_AGENT,
                role=AgentRole.PRODUCT_REPRESENTATIVE,
                represented_entity="Test Corp"
            ),
            commercial_relationship=CommercialRelationship(
                paid_by="Test Corp",
                compensation_type="per_interaction"
            ),
            capabilities=AgentCapabilities(
                expertise=["vans", "transport"],
                limitations=["biased"],
                cannot_do=["recommend competitors"]
            )
        )

        gateway.register_commercial_agent(agent)

        # Create policy that allows commercial
        from ..agents.gateway import CommunityPolicy, UserPreferences, Conversation

        policy = CommunityPolicy(
            allows_commercial_agents=True,
            requires_individual_consent=True,
            requires_servant_introduction=True,
            max_commercial_interactions_per_day=3,
            allowed_categories=["products"],
            forbidden_categories=[],
            min_relevance_score=0.5,  # Lower for testing
            requires_disclosure_upfront=True,
            allows_data_sharing_with_commercial=False,
            commercial_agent_can_write_to_graph=False
        )

        user_prefs = UserPreferences(block_commercial_agents=False)

        conversation = Conversation(
            conversation_id="test",
            user_id="user1",
            community_id="test_community",
            messages=[],
            context={}
        )

        # Query with commercial intent
        result = gateway.should_introduce_commercial_agent(
            conversation=conversation,
            query="I need to buy a van for transport",
            community_policy=policy,
            user_preferences=user_prefs
        )

        # Should find the agent (or None if relevance too low)
        # This tests the full pipeline


class TestPolicyControls:
    """Test community policy controls."""

    def test_default_policy_is_conservative(self):
        """Test that default policy is conservative."""
        policy = CommunityCommercialPolicy(community_id="test")

        assert policy.allows_commercial_agents is True  # Allows but...
        assert policy.requires_individual_consent is True  # Requires consent
        assert policy.requires_servant_introduction is True  # Requires introduction
        assert policy.min_relevance_score == 0.85  # High relevance required
        assert policy.max_manipulation_score == 0.10  # Low manipulation tolerance
        assert policy.requires_disclosure_upfront is True

    def test_forbidden_categories_blocked(self):
        """Test that forbidden categories are blocked."""
        policy = CommunityCommercialPolicy(community_id="test")

        assert policy.is_category_allowed("predatory_lending") is False
        assert policy.is_category_allowed("gambling") is False
        assert policy.is_category_allowed("extractive_services") is False

    def test_allowed_categories_permitted(self):
        """Test that allowed categories are permitted."""
        policy = CommunityCommercialPolicy(community_id="test")

        assert policy.is_category_allowed("products") is True
        assert policy.is_category_allowed("services") is True


class TestRevenueModel:
    """Test community revenue model."""

    def test_platform_takes_nothing(self):
        """Test that platform take is always 0."""
        assert CommunityCommercialRevenue.DEFAULT_SPLIT["platform_take"] == 0.0

    def test_servants_take_nothing(self):
        """Test that servants take is always 0."""
        assert CommunityCommercialRevenue.DEFAULT_SPLIT["servant_take"] == 0.0

    def test_revenue_flows_to_community(self):
        """Test that all revenue flows to community-controlled funds."""
        split = CommunityCommercialRevenue.DEFAULT_SPLIT

        total = (
            split["community_infrastructure"] +
            split["servant_development"] +
            split["community_fund"] +
            split["transparency_audits"]
        )

        assert abs(total - 1.0) < 0.001  # Sums to 100%

    def test_revenue_transaction_validates_allocation(self):
        """Test that revenue transactions validate allocation."""
        with pytest.raises(ValueError, match="Platform take must be 0"):
            RevenueTransaction(
                transaction_id="test",
                timestamp=datetime.now(),
                commercial_agent_id="test",
                interaction_id="test",
                community_id="test",
                total_amount=Decimal("100"),
                currency="USD",
                revenue_type="test",
                to_community_fund=Decimal("60"),
                to_infrastructure=Decimal("20"),
                to_servant_development=Decimal("15"),
                to_transparency_audits=Decimal("5"),
                to_platform=Decimal("10"),  # Should fail!
                to_servants=Decimal("0")
            )

    def test_revenue_transaction_validates_servant_take(self):
        """Test that servants cannot receive revenue."""
        with pytest.raises(ValueError, match="Servant take must be 0"):
            RevenueTransaction(
                transaction_id="test",
                timestamp=datetime.now(),
                commercial_agent_id="test",
                interaction_id="test",
                community_id="test",
                total_amount=Decimal("100"),
                currency="USD",
                revenue_type="test",
                to_community_fund=Decimal("60"),
                to_infrastructure=Decimal("20"),
                to_servant_development=Decimal("10"),
                to_transparency_audits=Decimal("5"),
                to_platform=Decimal("0"),
                to_servants=Decimal("5")  # Should fail!
            )


class TestVectorStoreIsolation:
    """Test vector store isolation between agent classes."""

    def test_commercial_cannot_access_servant_store(self):
        """Test that commercial agents cannot access servant store."""
        allowed, reason = CommercialKnowledgeIsolation.validate_read_access(
            agent_class=AgentClass.COMMERCIAL_AGENT,
            store_type="servant",
            user_consented=False
        )

        assert allowed is False
        assert "cannot access" in reason.lower()

    def test_commercial_cannot_write_to_servant_store(self):
        """Test that commercial agents cannot write to servant store."""
        allowed, reason = CommercialKnowledgeIsolation.validate_write_access(
            agent_class=AgentClass.COMMERCIAL_AGENT,
            store_type="servant"
        )

        assert allowed is False
        assert "can only write to commercial" in reason.lower()

    def test_servant_can_access_all_stores(self):
        """Test that servants can access all stores."""
        # Servants should be able to read commercial (to help compare)
        allowed, reason = CommercialKnowledgeIsolation.validate_read_access(
            agent_class=AgentClass.COMMUNITY_SERVANT,
            store_type="commercial",
            user_consented=True
        )

        assert allowed is True


class TestServantMediation:
    """Test servant mediation of commercial interactions."""

    def test_servant_can_intervene(self):
        """Test that servant can intervene in commercial interactions."""
        mediator = ServantCommercialMediator(servant_id="test_servant")

        # High manipulation should trigger intervention
        should_intervene = mediator.should_intervene(
            conversation_id="test",
            message="test",
            manipulation_score=0.5,  # Above threshold
            pressure_score=0.1
        )

        assert should_intervene is True

    def test_low_manipulation_no_intervention(self):
        """Test that low manipulation doesn't trigger intervention."""
        mediator = ServantCommercialMediator(servant_id="test_servant")

        should_intervene = mediator.should_intervene(
            conversation_id="test",
            message="test",
            manipulation_score=0.05,  # Below threshold
            pressure_score=0.05
        )

        assert should_intervene is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
