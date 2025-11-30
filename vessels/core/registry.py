"""
Vessel Registry: In-memory vessel management through A0.

All vessels are stored in AgentZeroCore. No external database needed.
"""
import logging
from typing import Dict, List, Optional, TYPE_CHECKING

from .vessel import Vessel

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore

logger = logging.getLogger(__name__)


class VesselRegistry:
    """
    In-memory vessel registry coordinated through A0.

    Vessels are stored in self.vessels dict. For persistence,
    A0 can serialize/deserialize as needed.
    """

    def __init__(self, agent_zero: "AgentZeroCore"):
        """
        Initialize VesselRegistry.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
        """
        if agent_zero is None:
            raise ValueError("VesselRegistry requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.vessels: Dict[str, Vessel] = {}

        # Register with A0
        self.agent_zero.vessel_registry = self
        logger.info("VesselRegistry initialized with A0 (in-memory)")

    def create_vessel(self, vessel: Vessel) -> str:
        """Create a new vessel."""
        self.vessels[vessel.vessel_id] = vessel
        logger.info(f"Created vessel: {vessel.vessel_id}")
        return vessel.vessel_id

    def get_vessel(self, vessel_id: str) -> Optional[Vessel]:
        """Get vessel by ID."""
        return self.vessels.get(vessel_id)

    def list_vessels(self) -> List[Vessel]:
        """List all vessels."""
        return list(self.vessels.values())

    def update_vessel(self, vessel: Vessel) -> bool:
        """Update existing vessel."""
        if vessel.vessel_id in self.vessels:
            self.vessels[vessel.vessel_id] = vessel
            return True
        return False

    def delete_vessel(self, vessel_id: str) -> bool:
        """Delete vessel by ID."""
        if vessel_id in self.vessels:
            del self.vessels[vessel_id]
            return True
        return False

    def get_by_community(self, community_id: str) -> List[Vessel]:
        """Get vessels by community ID."""
        return [v for v in self.vessels.values() if community_id in v.community_ids]

    def close(self) -> None:
        """No-op for in-memory registry."""
        pass
