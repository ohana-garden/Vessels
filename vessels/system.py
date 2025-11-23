"""
Vessels System Bootstrap: The Clean Entrypoint
"""
import logging
from typing import Dict, Any, List

from vessels.core.registry import VesselRegistry
from vessels.core.vessel import Vessel, PrivacyLevel
# Stub imports for components that should exist but might need integration
from kala import KalaValueSystem
# from vessels.gating.gate import ActionGate # Enable when you are ready to enforce ethics

logger = logging.getLogger(__name__)

class VesselsSystem:
    def __init__(self, db_path: str = "vessels_metadata.db"):
        self.registry = VesselRegistry(db_path=db_path)
        self.kala = KalaValueSystem()

        # Bootstrap
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
        This replaces the if/elif soup in the web server.
        """
        logger.info(f"Processing request for {session_id}: {text[:30]}...")

        intent = self._infer_intent(text)

        # TODO: Add Moral Gating Here
        # self.gate.check(intent)

        # Dispatch
        result = self._dispatch_agent(intent, text)

        # Record Value
        self.kala.record_contribution(
            contributor_id=result['agent'],
            contribution_type="service",
            description=f"Handled {intent}",
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
        In the future, this calls the LLM Router.
        For now, it returns structured data for the UI.
        """
        if intent == 'finance':
            return {
                "agent": "GrantFinder",
                "content_type": "grant_cards",
                "data": [
                    # Real implementation would query vector DB here
                    {'title': 'Older Americans Act (Real DB Fetch Pending)', 'amount': '$50k', 'funder': 'ACL'}
                ]
            }
        elif intent == 'care':
            return {
                "agent": "ElderSpecialist",
                "content_type": "care_protocol",
                "data": {"title": "Protocol Generation Active", "steps": []}
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
