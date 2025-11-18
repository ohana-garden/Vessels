"""
Grant Writer Tool
Generates complete grant applications
"""
from python.helpers.tool import Tool, Response
from python.helpers import files
import sys
import os

# Add shoghi to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from shoghi.applications.grants.grant_coordination_system import GrantCoordinator
from shoghi.applications.content.content_generation import ContentGenerator


class GrantWriter(Tool):
    """
    Tool for writing grant applications

    Use this tool to:
    - Generate complete grant narratives
    - Create culturally-adapted application content
    - Ensure compliance with grant requirements
    - Produce ready-to-submit applications
    """

    async def execute(self, **kwargs):
        """
        Execute grant writing

        Args:
            grant_title: Title of the grant opportunity
            program_description: Description of your program
            target_population: Who will benefit (e.g., "Hawaiian elders")
            cultural_context: Cultural framework (e.g., "Hawaiian", "multicultural")
            amount_requested: Amount to request
        """

        # Get parameters
        grant_title = self.args.get("grant_title", "")
        program_description = self.args.get("program_description", "")
        target_population = self.args.get("target_population", "")
        cultural_context = self.args.get("cultural_context", "multicultural")
        amount_requested = self.args.get("amount_requested")

        if not grant_title or not program_description:
            return Response(
                message="Error: grant_title and program_description are required",
                break_loop=False
            )

        # Log the writing process
        await self.agent.context.log.log(
            type="tool",
            heading=f"✍️ Writing grant application",
            content=f"Grant: {grant_title}\nPopulation: {target_population}",
        )

        try:
            # Initialize coordinator and content generator
            coordinator = GrantCoordinator()
            content_gen = ContentGenerator()

            # Generate grant narrative
            application_context = {
                'grant_title': grant_title,
                'program_description': program_description,
                'target_population': target_population,
                'cultural_context': cultural_context,
                'amount_requested': amount_requested
            }

            application = await coordinator.generate_application(application_context)

            # Adapt content to cultural context
            if cultural_context != "multicultural":
                adapted_content = content_gen.adapt_content(
                    content=application['narrative'],
                    culture=cultural_context,
                    audience='funders',
                    tone='formal'
                )
                application['narrative'] = adapted_content

            # Format the application
            result_text = f"# Grant Application: {grant_title}\n\n"
            result_text += f"## Executive Summary\n{application.get('summary', '')}\n\n"
            result_text += f"## Narrative\n{application.get('narrative', '')}\n\n"
            result_text += f"## Budget Overview\n{application.get('budget', '')}\n\n"
            result_text += f"## Compliance\n{application.get('compliance_notes', '')}\n\n"

            # Save to file
            filename = f"grant_application_{grant_title.replace(' ', '_').lower()}.md"
            files.write_file(
                files.get_abs_path(f"./memory/{filename}"),
                result_text
            )

            result_msg = f"Grant application generated successfully!\n\n"
            result_msg += f"Saved to: memory/{filename}\n\n"
            result_msg += f"Preview:\n{result_text[:500]}...\n\n"
            result_msg += "Use this as a starting point and customize as needed."

            return Response(
                message=result_msg,
                break_loop=False
            )

        except Exception as e:
            error_msg = f"Grant writing error: {str(e)}"
            await self.agent.context.log.log(
                type="error",
                heading="Grant Writing Failed",
                content=error_msg,
            )
            return Response(message=error_msg, break_loop=False)
