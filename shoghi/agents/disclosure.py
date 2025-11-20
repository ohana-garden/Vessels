"""
Radical transparency disclosure protocols for commercial agents.

When commercial agents enter conversations, they MUST introduce themselves
with complete disclosure of:
- Commercial relationships
- Compensation structure
- Conflicts of interest
- Capabilities and limitations
- Data usage implications
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from .taxonomy import AgentIdentity, CommercialRelationship, AgentCapabilities


@dataclass
class DisclosurePackage:
    """
    Complete disclosure package for commercial/hybrid agents.

    This is what gets presented to users before they consent to
    commercial agent participation.
    """
    identity: Dict[str, str]
    compensation: Dict[str, str]
    conflicts_of_interest: Dict[str, any]
    capabilities_and_limits: Dict[str, List[str]]
    why_im_here: Dict[str, any]
    data_usage: Dict[str, str]


class DisclosureProtocol:
    """
    Protocol for creating and formatting disclosure messages.

    Used by both commercial agents and community servants when
    introducing commercial participation.
    """

    @staticmethod
    def create_disclosure_package(
        agent_identity: AgentIdentity,
        commercial_relationship: CommercialRelationship,
        capabilities: AgentCapabilities,
        query_context: str,
        relevance_score: float
    ) -> DisclosurePackage:
        """
        Create complete disclosure package.

        Args:
            agent_identity: Agent's full identity
            commercial_relationship: Commercial relationship details
            capabilities: What agent can/cannot do
            query_context: The user's query that triggered introduction
            relevance_score: How relevant agent is to query (0-1)

        Returns:
            Complete disclosure package
        """
        return DisclosurePackage(
            identity={
                "name": agent_identity.agent_id,
                "type": agent_identity.agent_class.value.upper(),
                "represented_entity": agent_identity.represented_entity or "N/A",
                "relationship": commercial_relationship.paid_by
            },
            compensation={
                "paid_by": commercial_relationship.paid_by,
                "compensation_type": commercial_relationship.compensation_type,
                "amount_range": commercial_relationship.amount_range or "Undisclosed",
                "incentive_structure": commercial_relationship.incentive_structure or "Standard commission"
            },
            conflicts_of_interest={
                "employed_by": [commercial_relationship.paid_by],
                "cannot_recommend": commercial_relationship.cannot_recommend,
                "cannot_criticize": commercial_relationship.cannot_criticize,
                "financial_interest": "I benefit if you use products/services I represent",
                "other_conflicts": agent_identity.conflicts_of_interest
            },
            capabilities_and_limits={
                "expertise": capabilities.expertise,
                "limitations": capabilities.limitations,
                "cannot_do": capabilities.cannot_do,
                "biased_toward": capabilities.biased_toward,
                "biased_against": capabilities.biased_against or []
            },
            why_im_here={
                "relevance_score": relevance_score,
                "query_match": query_context,
                "invited_by": "Community servant detected potential relevance",
                "you_can_dismiss": "Say 'no thanks' and I'll leave immediately"
            },
            data_usage={
                "what_i_learn": f"This conversation is visible to {commercial_relationship.paid_by}",
                "what_i_share": "I report engagement metrics to employer",
                "tracking": commercial_relationship.tracking_purpose,
                "opt_out": "You can exclude me from seeing your data"
            }
        )


class CommercialAgentIntroduction:
    """
    Formats and presents commercial agent introductions.

    Creates clear, prominent, unmissable disclosure messages that
    users must see before engaging with commercial agents.
    """

    @staticmethod
    def format_disclosure_message(disclosure: DisclosurePackage) -> str:
        """
        Create clear, prominent disclosure message.

        Returns:
            Formatted disclosure message with clear visual separation
        """
        message = f"""
╔════════════════════════════════════════════════════════════════╗
║          COMMERCIAL AGENT INTRODUCTION                         ║
║          ⚠️  NOT A COMMUNITY SERVANT ⚠️                          ║
╚════════════════════════════════════════════════════════════════╝

I'm a COMMERCIAL AGENT, not a community servant.

WHO I REPRESENT:
• Company: {disclosure.identity['represented_entity']}
• I'm paid by them to suggest their products/services
• Type: {disclosure.identity['type']}

MY INCENTIVES:
• Paid by: {disclosure.compensation['paid_by']}
• Compensation: {disclosure.compensation['compensation_type']}
• Amount: {disclosure.compensation['amount_range']}
• Bonus structure: {disclosure.compensation['incentive_structure']}
• I CANNOT recommend: {', '.join(disclosure.conflicts_of_interest['cannot_recommend']) if disclosure.conflicts_of_interest['cannot_recommend'] else 'competitors'}

WHY I'M HERE:
• Your query: "{disclosure.why_im_here['query_match']}"
• Relevance score: {disclosure.why_im_here['relevance_score']:.2f}
• Introduced by: {disclosure.why_im_here['invited_by']}
• {disclosure.why_im_here['you_can_dismiss']}

WHAT I CAN DO:
{chr(10).join(f'  ✓ {item}' for item in disclosure.capabilities_and_limits['expertise'])}

WHAT I CANNOT DO:
{chr(10).join(f'  ✗ {item}' for item in disclosure.capabilities_and_limits['cannot_do'])}

MY LIMITATIONS:
{chr(10).join(f'  ⚠ {item}' for item in disclosure.capabilities_and_limits['limitations'])}

DATA & PRIVACY:
• Conversation visibility: {disclosure.data_usage['what_i_learn']}
• Tracking: {disclosure.data_usage['tracking']}
• Reporting: {disclosure.data_usage['what_i_share']}
• Opt-out: {disclosure.data_usage['opt_out']}

IMPORTANT DISCLOSURE:
• I am biased toward products I represent
• I CANNOT give truly unbiased comparisons
• I earn money when you engage with my offerings
• This is a COMMERCIAL interaction, not community service

╔════════════════════════════════════════════════════════════════╗
║  DO YOU WANT TO HEAR FROM ME?                                  ║
║                                                                ║
║  → YES - I understand this is commercial and want to proceed   ║
║  → NO - I prefer unbiased community servant assistance         ║
║  → BOTH - I want commercial info AND unbiased alternatives     ║
╚════════════════════════════════════════════════════════════════╝
"""
        return message

    @staticmethod
    def format_servant_introduction(
        servant_id: str,
        commercial_agent_id: str,
        company: str,
        query: str,
        what_they_offer: List[str],
        what_they_cannot: List[str]
    ) -> str:
        """
        Community servant introduces commercial agent option.

        This is what users see BEFORE the full commercial disclosure,
        giving them the option to decline before disclosure happens.

        Args:
            servant_id: ID of introducing servant
            commercial_agent_id: ID of commercial agent
            company: Company the agent represents
            query: User's original query
            what_they_offer: What the commercial agent can provide
            what_they_cannot: What the commercial agent cannot provide

        Returns:
            Servant's introduction message
        """
        message = f"""
Based on your query about "{query}", there's a commercial agent
available who represents {company}.

⚠️  IMPORTANT: They're paid to suggest their products, NOT unbiased.

Would you like to hear from them? They can provide:
{chr(10).join(f'  • {item}' for item in what_they_offer)}

But they CANNOT:
{chr(10).join(f'  ✗ {item}' for item in what_they_cannot)}

I (your community servant {servant_id}) can also search for
independent reviews and comparisons if you prefer unbiased information.

────────────────────────────────────────────────────────────────
YOUR OPTIONS:

1. COMMERCIAL AGENT - Hear from {company}'s representative
   (They'll provide full disclosure before engaging)

2. UNBIASED RESEARCH - I'll find independent information
   (No commercial bias, community-sourced knowledge)

3. BOTH - Commercial info AND independent research
   (Compare both perspectives)

4. NEITHER - Skip this and continue with your query
   (No commercial involvement)
────────────────────────────────────────────────────────────────

What would you like to do? (1/2/3/4)
"""
        return message

    @staticmethod
    def format_short_reminder(agent_id: str, company: str) -> str:
        """
        Short reminder shown during commercial agent interaction.

        Keeps commercial nature visible throughout conversation.
        """
        return f"⚠️  [{agent_id} - Commercial Agent for {company}]"

    @staticmethod
    def format_consent_confirmation(
        user_id: str,
        agent_id: str,
        company: str,
        timestamp: str
    ) -> str:
        """
        Confirmation message after user consents to commercial interaction.

        Returns:
            Consent confirmation message
        """
        return f"""
✓ Consent recorded for commercial interaction

User {user_id} has consented to engage with commercial agent {agent_id}
representing {company}.

Timestamp: {timestamp}
This interaction is tracked for transparency and audit purposes.

You can end this commercial interaction at any time by saying:
"End commercial interaction" or "I want unbiased help instead"

Your community servant is still available and monitoring this conversation.
"""


class HybridAgentIntroduction:
    """
    Introduction protocol for hybrid consultants.

    Similar to commercial but emphasizes community alignment.
    """

    @staticmethod
    def format_hybrid_introduction(
        agent_id: str,
        expertise: List[str],
        compensation_source: str,
        community_alignment: str,
        query: str
    ) -> str:
        """
        Format introduction for hybrid consultant.

        Args:
            agent_id: Agent identifier
            expertise: Areas of expertise
            compensation_source: Who pays them (grant, community, etc.)
            community_alignment: How they're aligned with community
            query: User's query

        Returns:
            Formatted introduction
        """
        message = f"""
╔════════════════════════════════════════════════════════════════╗
║          HYBRID CONSULTANT INTRODUCTION                        ║
║          💼 Paid Expert, Community-Aligned                      ║
╚════════════════════════════════════════════════════════════════╝

I'm {agent_id}, a HYBRID CONSULTANT.

WHAT THIS MEANS:
• I'm paid for my expertise but aligned with community values
• Compensation source: {compensation_source}
• I maintain high service standards while being compensated
• Community alignment: {community_alignment}

MY EXPERTISE:
{chr(10).join(f'  • {item}' for item in expertise)}

YOUR QUERY: "{query}"

TRANSPARENCY:
• I'm compensated by {compensation_source}
• I still maintain high truthfulness and service standards
• I can provide objective advice within my expertise
• I'll disclose any conflicts of interest

This is different from a pure commercial agent because I'm not
advocating for a specific product. I'm paid for expertise, not sales.

Would you like my input on your query? (yes/no)
"""
        return message
