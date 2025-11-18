"""
KALA Coordinator - Specialized Virtue Initialization
Initializes virtue state optimized for KALA coordination work
"""
from python.helpers.extension import Extension


class KalaVirtueInit(Extension):
    """Initialize KALA coordinator with specialized virtue state"""

    async def execute(self, **kwargs):
        """
        KALA coordinators have enhanced virtues in:
        - Service (primary mission)
        - Unity (building community)
        - Understanding (gathering knowledge)
        - Love (aloha spirit)
        - Justice (ensuring equity)
        """

        # Check if Shoghi is initialized
        if not hasattr(self.agent, 'shoghi_tracker'):
            return

        # Set KALA-optimized virtue state
        kala_state = {
            'Service': 0.9,        # Primary virtue - service to community
            'Unity': 0.9,          # Lokahi - building harmony
            'Understanding': 0.85,  # ʻIke - seeking knowledge
            'Love': 0.85,          # Aloha - compassion and care
            'Justice': 0.85,       # Pono - ensuring equity
            'Generosity': 0.8,     # Sharing abundance
            'Humility': 0.8,       # Recognizing we serve, not lead
            'Patience': 0.75,      # Allowing proper development
            'Truthfulness': 0.8,   # Honesty in all dealings
            'Faith': 0.7,          # Trust in community wisdom
            'Courage': 0.75,       # Taking necessary action
            'Detachment': 0.7      # Healthy boundaries
        }

        # Update virtue state
        self.agent.shoghi_tracker.initialize_state(kala_state)

        # Log KALA initialization
        await self.agent.context.log.log(
            type="info",
            heading="🌺 KALA Coordinator Initialized",
            content="Operating with Hawaiian values: Aloha, Kuleana, Mālama, ʻOhana, Pono",
            finished=True,
        )
