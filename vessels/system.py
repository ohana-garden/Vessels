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
