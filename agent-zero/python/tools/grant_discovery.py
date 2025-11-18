"""
Grant Discovery Tool
Discovers grant opportunities based on user needs
"""
from python.helpers.tool import Tool, Response
from python.helpers import files
import sys
import os

# Add shoghi to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from shoghi.applications.grants.grant_coordination_system import GrantCoordinator


class GrantDiscovery(Tool):
    """
    Tool for discovering grant opportunities

    Use this tool to:
    - Find grant opportunities matching specific criteria
    - Search for funding in particular domains (elder care, community programs, etc.)
    - Get grant details including deadlines, amounts, and requirements
    """

    async def execute(self, **kwargs):
        """
        Execute grant discovery

        Args:
            focus: Main focus area (e.g., "elder care", "community health")
            location: Geographic location (e.g., "Hawaii", "Puna")
            amount_min: Minimum grant amount (optional)
            amount_max: Maximum grant amount (optional)
        """

        # Get parameters
        focus = self.args.get("focus", "community programs")
        location = self.args.get("location", "")
        amount_min = self.args.get("amount_min")
        amount_max = self.args.get("amount_max")

        # Log the search
        await self.agent.context.log.log(
            type="tool",
            heading=f"🔍 Searching for {focus} grants",
            content=f"Location: {location}\nAmount range: ${amount_min or 'any'} - ${amount_max or 'any'}",
        )

        try:
            # Initialize grant coordinator
            coordinator = GrantCoordinator()

            # Search for grants
            search_criteria = {
                'focus_area': focus,
                'geographic_area': location,
                'min_amount': amount_min,
                'max_amount': amount_max
            }

            grants = await coordinator.discover_grants(search_criteria)

            # Format results
            if grants:
                result_text = f"Found {len(grants)} grant opportunities:\n\n"
                for i, grant in enumerate(grants[:10], 1):  # Limit to top 10
                    result_text += f"{i}. **{grant['title']}**\n"
                    result_text += f"   - Amount: ${grant.get('amount', 'TBD')}\n"
                    result_text += f"   - Deadline: {grant.get('deadline', 'Rolling')}\n"
                    result_text += f"   - Funder: {grant.get('funder', 'Unknown')}\n"
                    result_text += f"   - Match: {grant.get('match_score', 0):.0%}\n\n"

                # Store grants in agent memory for later use
                self.agent.set_data("discovered_grants", grants[:10])

            else:
                result_text = f"No grants found matching criteria. Consider:\n"
                result_text += "- Broadening the focus area\n"
                result_text += "- Expanding geographic scope\n"
                result_text += "- Adjusting amount requirements"

            return Response(
                message=result_text,
                break_loop=False
            )

        except Exception as e:
            error_msg = f"Grant discovery error: {str(e)}"
            await self.agent.context.log.log(
                type="error",
                heading="Grant Discovery Failed",
                content=error_msg,
            )
            return Response(message=error_msg, break_loop=False)
