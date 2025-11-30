"""
Vessels System Bootstrap: The Clean Entrypoint

REQUIRES AgentZeroCore - all system operations are coordinated through A0.
"""
import logging
from typing import Dict, Any, List, TYPE_CHECKING

from vessels.core.registry import VesselRegistry
from vessels.core.vessel import Vessel, PrivacyLevel
# Import Kala directly assuming it's in the python path/root
from kala import KalaValueSystem, ContributionType

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore

logger = logging.getLogger(__name__)

class VesselsSystem:
    """
    Complete Vessels system orchestrator.

    REQUIRES AgentZeroCore - all system operations are coordinated through A0.
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        db_path: str = "vessels_metadata.db"
    ):
        """
        Initialize VesselsSystem.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            db_path: Path to SQLite database file
        """
        if agent_zero is None:
            raise ValueError("VesselsSystem requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.registry = VesselRegistry(agent_zero=agent_zero, db_path=db_path)
        self.kala = KalaValueSystem()

        # Register with A0
        self.agent_zero.vessels_system = self
        logger.info("VesselsSystem initialized with A0")

        # Bootstrap default vessel if none exists
        if not self.registry.list_vessels():
            self._bootstrap_default_vessel()

    def _bootstrap_default_vessel(self):
        logger.info("Bootstrapping default vessel...")
        self.registry.create_vessel(
            Vessel.create(
                name="Ohana Prime",
                community_id="ohana_garden_main",
                description="Root community vessel",
                privacy_level=PrivacyLevel.PRIVATE
            )
        )

    def process_request(self, text: str, session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main Pipeline: Intent -> Agent -> Action
        This logic replaces the hardcoded "grant" checks in the old web server.
        """
        logger.info(f"Processing request for {session_id}: {text[:30]}...")

        intent = self._infer_intent(text)

        # Future: Insert Moral Gating here
        # self.gate.check(intent)

        # Dispatch to appropriate agent
        result = self._dispatch_agent(intent, text)

        # Record Economic Value (Kala)
        self.kala.record_contribution(
            contributor_id=result['agent'],
            contribution_type=ContributionType.SKILL,
            description=f"Handled {intent} request",
            kala_value=0.5
        )

        return result

    def _infer_intent(self, text: str) -> str:
        text = text.lower()
        if any(w in text for w in ['grant', 'money', 'funding']): return 'finance'
        if any(w in text for w in ['elder', 'care', 'health']): return 'care'
        if any(w in text for w in ['food', 'eat', 'hungry']): return 'logistics'
        return 'general'

    def _dispatch_agent(self, intent: str, text: str) -> Dict[str, Any]:
        """
        Dispatch to specialized agents.
        In a full implementation, this would route to specific Agent instances.
        """
        if intent == 'finance':
            return {
                "agent": "GrantFinder",
                "content_type": "grant_cards",
                "data": [
                    {'title': 'Older Americans Act (System Fetch)', 'amount': '$50k', 'funder': 'ACL'},
                    {'title': 'Hawaii Community Fdn', 'amount': '$10k', 'funder': 'HCF'}
                ]
            }
        elif intent == 'care':
            return {
                "agent": "ElderSpecialist",
                "content_type": "care_protocol",
                "data": {"title": "Kupuna Care Protocol", "steps": ["Morning Check", "Medication Review"]}
            }

        return {
            "agent": "Host",
            "content_type": "chat",
            "data": {"message": f"I received your request: '{text}'. How can I help further?"}
        }

    def get_status(self):
        return {
            "vessels": len(self.registry.list_vessels()),
            "kala_accounts": len(self.kala.accounts),
            "status": "online (Clean Architecture)"
        }
