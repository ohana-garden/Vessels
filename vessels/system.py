"""
Vessels System Bootstrap: The Clean Entrypoint
"""
import logging
from typing import Dict, Any, List, Optional

from vessels.core.registry import VesselRegistry
from vessels.core.vessel import Vessel, PrivacyLevel
# Import Kala directly assuming it's in the python path/root
from kala import KalaValueSystem, ContributionType

logger = logging.getLogger(__name__)


def _create_action_gate():
    """Create the moral action gate with Bahá'í manifold constraints."""
    try:
        from vessels.gating.gate import ActionGate
        from vessels.constraints.bahai import BahaiManifold
        from vessels.measurement.operational import OperationalMetrics
        from vessels.measurement.virtue_inference import VirtueInferenceEngine

        manifold = BahaiManifold(include_operational_constraints=True)
        operational_metrics = OperationalMetrics()
        virtue_engine = VirtueInferenceEngine()

        return ActionGate(
            manifold=manifold,
            operational_metrics=operational_metrics,
            virtue_engine=virtue_engine,
            block_on_timeout=True
        )
    except Exception as e:
        logger.warning(f"Could not initialize moral gate: {e}")
        return None


class VesselsSystem:
    def __init__(self, db_path: str = "vessels_metadata.db"):
        self.registry = VesselRegistry(db_path=db_path)
        self.kala = KalaValueSystem()

        # Initialize moral gating
        self.gate = _create_action_gate()
        if self.gate:
            logger.info("Moral gating enabled with Bahá'í manifold")
        else:
            logger.warning("Running WITHOUT moral gating - for development only!")

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
        Main Pipeline: Intent -> Moral Gating -> Agent -> Action
        This logic replaces the hardcoded "grant" checks in the old web server.
        """
        logger.info(f"Processing request for {session_id}: {text[:30]}...")

        intent = self._infer_intent(text)

        # Build action for moral gating
        action = {
            "type": "request_handling",
            "intent": intent,
            "text": text,
            "session_id": session_id,
            "service_value": 0.7,  # Handling user requests is valuable
        }

        # Apply Moral Gating
        if self.gate:
            gating_result = self.gate.gate_action(
                agent_id=f"system_{session_id}",
                action=action,
                action_metadata={"context": context}
            )

            if not gating_result.allowed:
                logger.warning(f"Request blocked by moral gate: {gating_result.reason}")
                return {
                    "agent": "System",
                    "content_type": "blocked",
                    "data": {
                        "message": "I'm unable to process this request at this time.",
                        "reason": gating_result.reason
                    },
                    "gating_blocked": True
                }

            logger.debug(f"Request passed moral gate: {gating_result.reason}")

        # Dispatch to appropriate agent
        result = self._dispatch_agent(intent, text)

        # Calculate Kala value based on intent and complexity
        kala_value = self._calculate_kala_value(intent, text)

        # Record Economic Value (Kala)
        self.kala.record_contribution(
            contributor_id=result['agent'],
            contribution_type=ContributionType.SKILL,
            description=f"Handled {intent} request",
            kala_value=kala_value
        )

        result['kala_value'] = kala_value
        return result

    def _calculate_kala_value(self, intent: str, text: str) -> float:
        """Calculate Kala value based on intent and request complexity."""
        base_value = {
            'finance': 1.5,  # Finance help is high value
            'care': 2.0,     # Care support is highest value
            'logistics': 1.0,
            'general': 0.5
        }.get(intent, 0.5)

        # Complexity bonus based on text length
        complexity_bonus = min(len(text) / 500, 0.5)

        return base_value + complexity_bonus

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
