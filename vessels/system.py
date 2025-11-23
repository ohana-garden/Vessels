"""
Vessels System Bootstrap: The Clean Entrypoint
Replaces vessels_fixed.py with proper architectural separation
"""
import logging
from typing import Dict, Any, Optional

from vessels.core.registry import VesselRegistry
from vessels.core.vessel import Vessel, PrivacyLevel
from vessels.knowledge.schema import CommunityPrivacy

logger = logging.getLogger(__name__)

class VesselsSystem:
    """
    Clean system interface that properly integrates all Vessels components.
    This replaces the mock/hardcoded approach in vessels_fixed.py.
    """

    def __init__(self, db_path: str = "vessels_metadata.db"):
        """Initialize the Vessels system with proper component integration."""
        self.registry = VesselRegistry(db_path=db_path)

        # Initialize Kala if available
        try:
            from kala import KalaValueSystem
            self.kala = KalaValueSystem()
        except ImportError:
            logger.warning("Kala system not available")
            self.kala = None

        # Initialize Community Memory if available
        try:
            from community_memory import community_memory
            self.memory = community_memory
        except ImportError:
            logger.warning("Community Memory not available")
            self.memory = None

        # Bootstrap default vessel if none exists
        if not self.registry.list_vessels():
            self._bootstrap_default_vessel()

        logger.info("🌺 Vessels System initialized")

    def _bootstrap_default_vessel(self):
        """Create a default vessel if none exists."""
        logger.info("Bootstrapping default vessel...")
        vessel = Vessel.create(
            name="Ohana Prime",
            community_id="ohana_garden_main",
            description="Root community vessel",
            privacy_level=PrivacyLevel.PRIVATE
        )
        self.registry.create_vessel(vessel)

    def process_request(self, text: str, session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing pipeline:
        1. Intent Recognition
        2. Moral Gating (when implemented)
        3. Agent Dispatch
        4. Response Generation

        This is the clean replacement for the hardcoded if/else chains in the web server.
        """
        logger.info(f"Processing request for session {session_id}: {text[:50]}...")

        # 1. Intent Recognition (cleaner routing logic)
        intent = self._infer_intent(text)

        # 2. TODO: Moral Gating (ActionGate will go here)
        # from vessels.gating.gate import ActionGate
        # gate_result = self.gate.check(intent)
        # if not gate_result.allowed:
        #     return {"error": "Ethical constraint violation", "reason": gate_result.reason}

        # 3. Agent Dispatch
        response_data = self._dispatch_agent(intent, text, context)

        return response_data

    def _infer_intent(self, text: str) -> str:
        """
        Infer user intent from text input.
        In production, this would use an LLM or trained classifier.
        """
        text_lower = text.lower()

        # Finance/Grant intent
        if any(word in text_lower for word in ['grant', 'funding', 'money', 'finance']):
            return 'finance'

        # Elder care intent
        if any(word in text_lower for word in ['elder', 'care', 'kupuna', 'senior']):
            return 'care'

        # Food/logistics intent
        if any(word in text_lower for word in ['food', 'meal', 'delivery', 'transport']):
            return 'logistics'

        # Schedule intent
        if any(word in text_lower for word in ['schedule', 'time', 'when', 'available']):
            return 'schedule'

        # Help intent
        if any(word in text_lower for word in ['help', 'how', 'what']):
            return 'help'

        return 'general'

    def _dispatch_agent(self, intent: str, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch to appropriate agent based on intent.
        This replaces the hardcoded dictionaries in the web server.
        In production, this would call AgentZeroCore or similar.
        """

        if intent == 'finance':
            return self._handle_finance_request(text, context)

        elif intent == 'care':
            return self._handle_care_request(text, context)

        elif intent == 'logistics':
            return self._handle_logistics_request(text, context)

        elif intent == 'schedule':
            return self._handle_schedule_request(text, context)

        elif intent == 'help':
            return self._handle_help_request(text, context)

        return self._handle_general_request(text, context)

    def _handle_finance_request(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle grant/finance requests.
        TODO: Replace mock data with real grant system integration.
        """
        # TODO: Integrate with grant_coordination_fixed or real grant API
        grants = self._get_mock_grants()

        return {
            "agent": "GrantFinder",
            "content_type": "grant_cards",
            "data": {"grants": grants}
        }

    def _handle_care_request(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle elder care requests.
        TODO: Replace mock data with real care protocol generation.
        """
        protocol = self._get_mock_care_protocol()

        return {
            "agent": "ElderCareSpecialist",
            "content_type": "care_protocol",
            "data": protocol
        }

    def _handle_logistics_request(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle food/logistics requests.
        TODO: Integrate with real logistics coordination.
        """
        return {
            "agent": "LogisticsCoordinator",
            "content_type": "logistics_plan",
            "data": {"message": "Coordinating resources..."}
        }

    def _handle_schedule_request(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle scheduling requests.
        TODO: Integrate with real calendar system.
        """
        return {
            "agent": "ScheduleCoordinator",
            "content_type": "calendar_view",
            "data": {"message": "Checking availability..."}
        }

    def _handle_help_request(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle help requests."""
        return {
            "agent": "Host",
            "content_type": "help",
            "data": {
                "message": "I can help with grants, elder care, logistics, and scheduling.",
                "capabilities": [
                    "Grant discovery and application",
                    "Elder care coordination",
                    "Food and resource logistics",
                    "Volunteer scheduling"
                ]
            }
        }

    def _handle_general_request(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general conversation."""
        return {
            "agent": "Host",
            "content_type": "chat",
            "data": {"message": "I am listening. How can the community help?"}
        }

    # Mock data methods (these should be replaced with real integrations)

    def _get_mock_grants(self):
        """
        Mock grant data.
        TODO: Replace with actual grant_system.discover_grants() call
        """
        return [
            {
                'title': 'Older Americans Act',
                'amount': '$50K - $500K',
                'description': 'Federal funding for elder care services in rural communities.',
                'funder': 'Administration for Community Living'
            },
            {
                'title': 'Hawaii Community Foundation',
                'amount': '$10K - $50K',
                'description': 'Local funding for community-driven initiatives.',
                'funder': 'HCF'
            }
        ]

    def _get_mock_care_protocol(self):
        """
        Mock care protocol data.
        TODO: Replace with actual content_generator.generate_content() call
        """
        return {
            'title': 'Kupuna Care Protocol',
            'steps': [
                {
                    'title': 'Morning Check',
                    'description': 'Call or visit by 9am. Verify medications taken, breakfast eaten.'
                },
                {
                    'title': 'Midday Support',
                    'description': 'Lunch delivery if needed. Social interaction, talk story time.'
                },
                {
                    'title': 'Afternoon Tasks',
                    'description': 'Doctor appointments, shopping. Coordinate with family members.'
                },
                {
                    'title': 'Evening Safety',
                    'description': 'Dinner check, secure home. Emergency contacts confirmed.'
                }
            ]
        }

    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        vessels = self.registry.list_vessels()

        status = {
            "system": "online",
            "vessels": len(vessels),
            "components": {
                "registry": "operational",
                "kala": "operational" if self.kala else "unavailable",
                "memory": "operational" if self.memory else "unavailable"
            }
        }

        if self.kala:
            status["kala_accounts"] = len(self.kala.accounts)

        return status
