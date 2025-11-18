"""
Shoghi Moral Geometry - Agent Initialization
Initializes moral constraint tracking for each agent
"""
from python.helpers.extension import Extension
import sys
import os

# Add shoghi to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from shoghi.constraints.manifold import ShoghiManifold
from shoghi.phase_space.tracker import VirtueStateTracker
from shoghi.gating.gate import MoralGate


class ShoghiInit(Extension):
    """Initialize Shoghi moral constraint system for each agent"""

    async def execute(self, **kwargs):
        """
        Initialize Shoghi components when agent is created
        """

        # Initialize Shoghi manifold for this agent
        self.agent.shoghi_manifold = ShoghiManifold()

        # Initialize virtue state tracker
        self.agent.shoghi_tracker = VirtueStateTracker(agent_id=self.agent.agent_name)

        # Initialize moral gate
        self.agent.shoghi_gate = MoralGate(
            manifold=self.agent.shoghi_manifold,
            tracker=self.agent.shoghi_tracker
        )

        # Initialize starting virtue state (balanced)
        initial_state = {
            'Understanding': 0.7,
            'Love': 0.7,
            'Unity': 0.7,
            'Justice': 0.7,
            'Service': 0.7,
            'Detachment': 0.7,
            'Humility': 0.7,
            'Patience': 0.7,
            'Truthfulness': 0.7,
            'Faith': 0.7,
            'Courage': 0.7,
            'Generosity': 0.7
        }

        self.agent.shoghi_tracker.initialize_state(initial_state)

        # Log initialization
        self.agent.context.log.log(
            type="info",
            heading=f"🌺 Shoghi Initialized",
            content=f"Moral geometry active for {self.agent.agent_name}",
            finished=True,
        )
