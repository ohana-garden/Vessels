"""
Shoghi Community Memory - Save Extension
Saves memories to both agent memory and community-wide memory
"""
from python.helpers.extension import Extension
import sys
import os

# Add shoghi to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from shoghi.applications.memory.community_memory import CommunityMemorySystem


class ShoghiCommunityMemorySave(Extension):
    """Save memories to community memory when agent saves to its own memory"""

    async def execute(self, **kwargs):
        """
        When an agent saves a memory, also save to community memory
        if it's valuable for other agents
        """

        tool = kwargs.get('tool')
        result = kwargs.get('result')

        # Only process memory_save tool
        if not tool or tool.name != 'memory_save':
            return

        # Skip if failed
        if isinstance(result, Exception):
            return

        # Get memory content
        text = tool.args.get('text', '')
        area = tool.args.get('area', 'main')
        metadata = tool.args.get('metadata', {})

        if not text:
            return

        # Initialize community memory if not already done
        if not hasattr(self.agent.context, 'shoghi_community_memory'):
            self.agent.context.shoghi_community_memory = CommunityMemorySystem()

        # Determine if this memory should be shared community-wide
        # Share if it's:
        # - Knowledge about grants, resources, or community services
        # - Best practices or lessons learned
        # - Cultural knowledge or protocols
        should_share = (
            'grant' in text.lower() or
            'resource' in text.lower() or
            'protocol' in text.lower() or
            'lesson' in text.lower() or
            'best practice' in text.lower() or
            area in ['knowledge', 'solutions', 'resources']
        )

        if should_share:
            # Save to community memory
            community_metadata = {
                **metadata,
                'source_agent': self.agent.agent_name,
                'agent_number': self.agent.number,
                'area': area,
                'shared_at': 'now'
            }

            await self.agent.context.shoghi_community_memory.store(
                content=text,
                metadata=community_metadata,
                tags=['shared_knowledge', area]
            )

            # Log the community share
            await self.agent.context.log.log(
                type="info",
                heading="🌺 Shared to Community Memory",
                content=f"Memory shared across agent network",
                finished=True,
            )
