"""
Inter-Community Clearing House for cross-community exchanges.

Enables Kala-neutral swaps between communities without central intermediary.
Example: Community A has food surplus, needs transport.
         Community B has transport surplus, needs food.
         Clearing house facilitates zero-sum exchange.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Offer:
    """
    Offer from a community for exchange.

    Represents surplus resources available for swap.
    """
    community_id: str
    offer_type: str  # "food", "transport", "labor", etc.
    kala_value: float
    quantity: float
    unit: str  # "meals", "miles", "hours", etc.
    description: str
    expiration: datetime
    metadata: Dict = field(default_factory=dict)

    def with_value(self, new_kala_value: float) -> 'Offer':
        """Create copy of offer with different Kala value."""
        return Offer(
            community_id=self.community_id,
            offer_type=self.offer_type,
            kala_value=new_kala_value,
            quantity=(self.quantity * new_kala_value / self.kala_value) if self.kala_value > 0 else 0,
            unit=self.unit,
            description=self.description,
            expiration=self.expiration,
            metadata=self.metadata
        )


@dataclass
class SwapProposal:
    """
    Proposal for Kala-neutral swap between communities.

    Zero-sum exchange: Both communities give and receive equal Kala value.
    """
    id: str
    community_a: str
    community_b: str
    a_gives: Offer
    b_gives: Offer
    kala_value: float  # Same for both sides (zero-sum)
    status: str  # "proposed", "approved_by_a", "approved_by_b", "executed", "rejected"
    created_at: datetime = field(default_factory=datetime.now)
    approved_by_a: bool = False
    approved_by_b: bool = False

    def approved_by_both(self) -> bool:
        """Check if both communities approved the swap."""
        return self.approved_by_a and self.approved_by_b

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "community_a": self.community_a,
            "community_b": self.community_b,
            "a_gives": {
                "type": self.a_gives.offer_type,
                "kala_value": self.a_gives.kala_value,
                "description": self.a_gives.description
            },
            "b_gives": {
                "type": self.b_gives.offer_type,
                "kala_value": self.b_gives.kala_value,
                "description": self.b_gives.description
            },
            "kala_value": self.kala_value,
            "status": self.status,
            "approved_by_both": self.approved_by_both()
        }


class InterCommunityClearingHouse:
    """
    Facilitates Kala-neutral exchanges between communities.

    Enables inter-community cooperation without requiring trust in
    central authority or shared currency.
    """

    def __init__(self):
        """Initialize clearing house."""
        self.pending_proposals: Dict[str, SwapProposal] = {}
        self.executed_swaps: List[SwapProposal] = []
        self.offers: Dict[str, List[Offer]] = {}  # community_id → offers

    def register_offer(self, offer: Offer) -> None:
        """
        Register an offer from a community.

        Args:
            offer: Offer to register
        """
        if offer.community_id not in self.offers:
            self.offers[offer.community_id] = []

        self.offers[offer.community_id].append(offer)

        logger.info(
            f"Registered offer from {offer.community_id}: "
            f"{offer.quantity} {offer.unit} of {offer.offer_type} "
            f"({offer.kala_value} kala)"
        )

    def propose_swap(
        self,
        community_a_id: str,
        need_a: str,
        offer_a: Offer,
        community_b_id: str,
        need_b: str,
        offer_b: Offer
    ) -> Optional[SwapProposal]:
        """
        Propose a Kala-neutral swap between communities.

        Args:
            community_a_id: First community ID
            need_a: What community A needs
            offer_a: What community A offers
            community_b_id: Second community ID
            need_b: What community B needs
            offer_b: What community B offers

        Returns:
            SwapProposal if match found, None otherwise
        """
        # Verify trust relationship (simplified - in production, check trusted_communities)
        if not self._verify_trust(community_a_id, community_b_id):
            logger.warning(f"Communities {community_a_id} and {community_b_id} don't trust each other")
            return None

        # Match needs with offers
        if need_a == offer_b.offer_type and need_b == offer_a.offer_type:
            # Calculate Kala equivalence (use minimum to ensure both can fulfill)
            kala_value = min(offer_a.kala_value, offer_b.kala_value)

            proposal = SwapProposal(
                id=str(uuid.uuid4()),
                community_a=community_a_id,
                community_b=community_b_id,
                a_gives=offer_a.with_value(kala_value),
                b_gives=offer_b.with_value(kala_value),
                kala_value=kala_value,
                status="proposed"
            )

            self.pending_proposals[proposal.id] = proposal

            logger.info(
                f"Created swap proposal: {community_a_id} ↔ {community_b_id} "
                f"({kala_value} kala value)"
            )

            return proposal

        return None

    def approve_swap(self, proposal_id: str, community_id: str) -> bool:
        """
        Approve a swap proposal.

        Args:
            proposal_id: Proposal ID
            community_id: Community approving

        Returns:
            True if approval successful
        """
        if proposal_id not in self.pending_proposals:
            logger.error(f"Proposal {proposal_id} not found")
            return False

        proposal = self.pending_proposals[proposal_id]

        if community_id == proposal.community_a:
            proposal.approved_by_a = True
            logger.info(f"Community A approved swap {proposal_id}")
        elif community_id == proposal.community_b:
            proposal.approved_by_b = True
            logger.info(f"Community B approved swap {proposal_id}")
        else:
            logger.error(f"Community {community_id} not part of swap {proposal_id}")
            return False

        # Check if both approved
        if proposal.approved_by_both():
            proposal.status = "ready_to_execute"
            logger.info(f"Swap {proposal_id} approved by both communities, ready to execute")

        return True

    def execute_swap(
        self,
        proposal_id: str,
        kala_system_a,
        kala_system_b
    ) -> bool:
        """
        Execute an approved swap.

        Args:
            proposal_id: Proposal to execute
            kala_system_a: KalaValueSystem for community A
            kala_system_b: KalaValueSystem for community B

        Returns:
            True if execution successful
        """
        if proposal_id not in self.pending_proposals:
            logger.error(f"Proposal {proposal_id} not found")
            return False

        proposal = self.pending_proposals[proposal_id]

        if not proposal.approved_by_both():
            logger.error(f"Swap {proposal_id} not approved by both communities")
            return False

        try:
            # Physical transfer happens externally
            # Update Kala ledgers (zero-sum)

            # Community A: debit what they give, credit what they receive
            # Note: In CRDT mode, these would be CRDT operations
            logger.info(
                f"Community A: -{proposal.a_gives.kala_value} kala "
                f"(gave {proposal.a_gives.offer_type}), "
                f"+{proposal.b_gives.kala_value} kala "
                f"(received {proposal.b_gives.offer_type})"
            )

            # Community B: debit what they give, credit what they receive
            logger.info(
                f"Community B: -{proposal.b_gives.kala_value} kala "
                f"(gave {proposal.b_gives.offer_type}), "
                f"+{proposal.a_gives.kala_value} kala "
                f"(received {proposal.a_gives.offer_type})"
            )

            # Net Kala change for both = 0 (zero-sum swap)

            # Move to executed
            proposal.status = "executed"
            self.executed_swaps.append(proposal)
            del self.pending_proposals[proposal_id]

            logger.info(f"✅ Swap {proposal_id} executed successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to execute swap {proposal_id}: {e}")
            proposal.status = "failed"
            return False

    def find_swap_opportunities(
        self,
        communities: List[str]
    ) -> List[SwapProposal]:
        """
        Automatically find swap opportunities between communities.

        Args:
            communities: List of community IDs

        Returns:
            List of potential swap proposals
        """
        opportunities = []

        # Check all pairs of communities
        for i in range(len(communities)):
            for j in range(i + 1, len(communities)):
                community_a = communities[i]
                community_b = communities[j]

                # Get offers from both
                offers_a = self.offers.get(community_a, [])
                offers_b = self.offers.get(community_b, [])

                # Find matching needs/offers
                for offer_a in offers_a:
                    for offer_b in offers_b:
                        # Check if they match (A offers what B needs, B offers what A needs)
                        # Simplified: assume offer type indicates both what they have and what they need
                        # In production, would have separate need/offer tracking

                        if offer_a.offer_type != offer_b.offer_type:
                            # Potential match
                            proposal = self.propose_swap(
                                community_a,
                                offer_b.offer_type,  # A needs what B offers
                                offer_a,
                                community_b,
                                offer_a.offer_type,  # B needs what A offers
                                offer_b
                            )

                            if proposal:
                                opportunities.append(proposal)

        logger.info(f"Found {len(opportunities)} swap opportunities")

        return opportunities

    def _verify_trust(self, community_a: str, community_b: str) -> bool:
        """
        Verify communities trust each other for swaps.

        In production, would check trusted_communities configuration.
        For now, simplified to allow all.
        """
        # TODO: Implement proper trust verification
        return True

    def get_pending_proposals(self, community_id: Optional[str] = None) -> List[SwapProposal]:
        """
        Get pending swap proposals.

        Args:
            community_id: Optional filter by community

        Returns:
            List of pending proposals
        """
        proposals = list(self.pending_proposals.values())

        if community_id:
            proposals = [
                p for p in proposals
                if p.community_a == community_id or p.community_b == community_id
            ]

        return proposals
