"""
Vessels System Bootstrap: The Clean Entrypoint
Replaces vessels_fixed.py with proper architectural separation

Now with FalkorDB-first architecture for maximum off-device processing.
"""
import logging
import os
from typing import Dict, Any, Optional

from vessels.core.registry import VesselRegistry
from vessels.core.vessel import Vessel, PrivacyLevel
from vessels.knowledge.schema import CommunityPrivacy
from vessels.storage.session import create_session_store, SessionStore
from vessels.database.falkordb_client import get_falkordb_client, FalkorDBClient

logger = logging.getLogger(__name__)

class VesselsSystem:
    """
    Clean system interface that properly integrates all Vessels components.

    Now FalkorDB-first: All data and processing offloaded to graph database
    for minimal on-device footprint and maximum scalability.
    """

    def __init__(
        self,
        db_path: str = "vessels_metadata.db",
        session_store_type: str = "falkordb",  # Changed default to FalkorDB
        enable_gating: bool = False,
        use_falkordb: bool = True,  # New: Enable FalkorDB by default
        falkordb_host: Optional[str] = None,
        falkordb_port: Optional[int] = None,
        **session_kwargs
    ):
        """
        Initialize the Vessels system with proper component integration.

        Args:
            db_path: Path to vessel registry database (legacy)
            session_store_type: Type of session store ("memory", "redis", "falkordb")
            enable_gating: Enable moral gating (requires full stack)
            use_falkordb: Use FalkorDB for all graph operations (default: True)
            falkordb_host: FalkorDB host (default: from env or localhost)
            falkordb_port: FalkorDB port (default: from env or 6379)
            **session_kwargs: Additional arguments for session store
        """
        # Initialize FalkorDB client if enabled
        self.falkordb_client: Optional[FalkorDBClient] = None
        self.use_falkordb = use_falkordb

        if use_falkordb:
            try:
                self.falkordb_client = get_falkordb_client(
                    host=falkordb_host or os.getenv("REDIS_HOST", "localhost"),
                    port=falkordb_port or int(os.getenv("REDIS_PORT", 6379))
                )
                logger.info("✅ FalkorDB client initialized - graph database active")
            except Exception as e:
                logger.error(f"Failed to initialize FalkorDB: {e}")
                logger.warning("Falling back to in-memory/SQLite mode")
                self.use_falkordb = False
                self.falkordb_client = None

        # Initialize registry
        self.registry = VesselRegistry(db_path=db_path)

        # Initialize session store (with FalkorDB if available)
        if use_falkordb and self.falkordb_client:
            session_kwargs["falkor_client"] = self.falkordb_client
        self.session_store = create_session_store(session_store_type, **session_kwargs)

        self.gating_enabled = enable_gating
        self.gate = None

        # Initialize FalkorDB-based components
        self.phase_space_tracker = None
        self.community_memory = None
        self.kala_network = None
        self.commercial_tracker = None
        self.grants_discovery = None

        if self.use_falkordb and self.falkordb_client:
            self._initialize_falkordb_components()

        # Fallback to legacy components if FalkorDB unavailable
        if not self.use_falkordb:
            self._initialize_legacy_components()

        # Initialize ActionGate if enabled and components available
        if enable_gating:
            self._initialize_action_gate()

        # Bootstrap default vessel if none exists
        if not self.registry.list_vessels():
            self._bootstrap_default_vessel()

        logger.info(
            f"🌺 Vessels System initialized "
            f"(FalkorDB={'✅' if self.use_falkordb else '❌'}, "
            f"session={session_store_type}, "
            f"gating={'enabled' if self.gate else 'disabled'})"
        )

    def _initialize_falkordb_components(self):
        """
        Initialize all FalkorDB-based components for off-device processing.
        """
        try:
            # Phase Space Tracker
            from vessels.phase_space.falkordb_tracker import FalkorDBPhaseSpaceTracker
            self.phase_space_tracker = FalkorDBPhaseSpaceTracker(self.falkordb_client)
            logger.info("✅ Phase Space Tracker initialized (FalkorDB)")

            # Community Memory
            from vessels.memory.falkordb_memory import FalkorDBCommunityMemory
            self.community_memory = FalkorDBCommunityMemory(self.falkordb_client)
            logger.info("✅ Community Memory initialized (FalkorDB)")

            # Kala Network
            from kala.falkordb_kala import FalkorDBKalaNetwork
            self.kala_network = FalkorDBKalaNetwork(self.falkordb_client)
            logger.info("✅ Kala Network initialized (FalkorDB)")

            # Commercial Agent Tracker
            from vessels.agents.graph_tracking import CommercialRelationshipGraph
            self.commercial_tracker = CommercialRelationshipGraph(self.falkordb_client)
            logger.info("✅ Commercial Tracker initialized (FalkorDB)")

            # Grants Discovery
            from grants.falkordb_grants import FalkorDBGrantsDiscovery
            self.grants_discovery = FalkorDBGrantsDiscovery(self.falkordb_client)
            logger.info("✅ Grants Discovery initialized (FalkorDB)")

            logger.info("🚀 All FalkorDB components active - maximum off-device processing")

        except ImportError as e:
            logger.warning(f"Some FalkorDB components unavailable: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize FalkorDB components: {e}")

    def _initialize_legacy_components(self):
        """
        Initialize legacy in-memory/SQLite components as fallback.
        """
        logger.warning("⚠️  Using legacy in-memory components - data will not persist")

        # Initialize Kala if available
        try:
            from kala import KalaValueSystem
            self.kala = KalaValueSystem()
            logger.info("Kala Value System initialized (in-memory)")
        except ImportError:
            logger.warning("Kala system not available")
            self.kala = None

        # Initialize Community Memory if available
        try:
            from community_memory import community_memory
            self.memory = community_memory
            logger.info("Community Memory initialized (in-memory)")
        except ImportError:
            logger.warning("Community Memory not available")
            self.memory = None

    def _initialize_action_gate(self):
        """
        Initialize the ActionGate for moral constraint enforcement.
        Requires full measurement stack to be available.
        """
        try:
            from vessels.gating.gate import ActionGate
            from vessels.constraints.bahai import BahaiManifold
            from vessels.measurement.operational import OperationalMetrics
            from vessels.measurement.virtue_inference import VirtueInferenceEngine

            # Create manifold
            manifold = BahaiManifold()

            # Create operational metrics tracker
            operational_metrics = OperationalMetrics()

            # Create virtue inference engine
            virtue_engine = VirtueInferenceEngine()

            # Create gate
            self.gate = ActionGate(
                manifold=manifold,
                operational_metrics=operational_metrics,
                virtue_engine=virtue_engine,
                latency_budget_ms=100.0,
                block_on_timeout=True,
                max_consecutive_blocks=5
            )

            logger.info("✅ ActionGate initialized - moral constraints active")

        except ImportError as e:
            logger.warning(
                f"ActionGate not available: {e}. "
                f"Moral gating disabled. System running WITHOUT ethical constraints."
            )
            self.gate = None
            self.gating_enabled = False

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

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get an existing session or create a new one.

        Args:
            session_id: Session identifier

        Returns:
            Session data dictionary
        """
        session = self.session_store.get_session(session_id)

        if not session:
            session = {
                'history': [],
                'emotion_history': [],
                'context': {}
            }
            self.session_store.create_session(session_id, session)

        return session

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update session data.

        Args:
            session_id: Session identifier
            data: Data to update

        Returns:
            True if successful
        """
        return self.session_store.update_session(session_id, data)

    def process_request(self, text: str, session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing pipeline:
        1. Intent Recognition
        2. Moral Gating (if enabled)
        3. Agent Dispatch
        4. Response Generation

        This is the clean replacement for the hardcoded if/else chains in the web server.
        """
        logger.info(f"Processing request for session {session_id}: {text[:50]}...")

        # 1. Intent Recognition
        intent = self._infer_intent(text)

        # 2. Moral Gating (if enabled)
        if self.gating_enabled and self.gate:
            action_metadata = {
                "intent": intent,
                "text": text,
                "session_id": session_id
            }

            gate_result = self.gate.gate_action(
                agent_id=f"session_{session_id}",
                action={"type": "process_request", "intent": intent, "text": text},
                action_metadata=action_metadata
            )

            if not gate_result.allowed:
                logger.warning(
                    f"Request blocked by ActionGate: {gate_result.reason} "
                    f"(session={session_id})"
                )
                return {
                    "error": "Request blocked by ethical constraints",
                    "reason": gate_result.reason,
                    "agent": "ActionGate",
                    "content_type": "error",
                    "data": {
                        "message": gate_result.reason,
                        "security_event": gate_result.security_event.to_dict() if gate_result.security_event else None
                    }
                }

            logger.debug(f"Request passed ActionGate: {gate_result.reason}")

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
