"""
Shoghi Community Memory - Load Enhancement
Enhances memory_load to also search community memory
"""
from python.helpers.extension import Extension
import sys
import os

# Add shoghi to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from shoghi.applications.memory.community_memory import CommunityMemorySystem


class ShoghiCommunityMemoryLoad(Extension):
    """Enhance memory_load to also search community-wide memory"""

    async def execute(self, **kwargs):
        """
        Before loading memories, check community memory too
        This happens BEFORE the tool executes, so we can enhance the search
        """

        tool = kwargs.get('tool')

        # Only process memory_load tool
        if not tool or tool.name != 'memory_load':
            return

        # Initialize community memory if not already done
        if not hasattr(self.agent.context, 'shoghi_community_memory'):
            self.agent.context.shoghi_community_memory = CommunityMemorySystem()

        # Get search query
        query = tool.args.get('query', '')

        if not query:
            return

        # Search community memory
        community_results = await self.agent.context.shoghi_community_memory.search(
            query=query,
            limit=5,
            filter={'exclude_agent': self.agent.agent_name}  # Exclude own memories
        )

        # Store community results for the tool to use
        if community_results:
            # Store in agent data for the memory_load tool to access
            self.agent.set_data('community_memory_results', community_results)

            # Log community memory access
            await self.agent.context.log.log(
                type="info",
                heading="🌺 Accessing Community Memory",
                content=f"Found {len(community_results)} relevant memories from other agents",
                finished=True,
            )
