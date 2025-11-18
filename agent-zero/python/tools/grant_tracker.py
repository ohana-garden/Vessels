"""
Grant Tracker Tool
Tracks grant application status and deadlines
"""
from python.helpers.tool import Tool, Response
import sys
import os
from datetime import datetime, timedelta

# Add shoghi to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from shoghi.applications.grants.grant_coordination_system import GrantCoordinator


class GrantTracker(Tool):
    """
    Tool for tracking grant applications

    Use this tool to:
    - Monitor grant application status
    - Track upcoming deadlines
    - Get status reports on submitted grants
    - Receive alerts for time-sensitive actions
    """

    async def execute(self, **kwargs):
        """
        Execute grant tracking

        Args:
            action: Action to perform ('add', 'status', 'deadlines', 'update')
            grant_title: Title of grant (for add/update)
            deadline: Deadline date (for add) - format: YYYY-MM-DD
            status: Current status (for update)
        """

        action = self.args.get("action", "status")
        grant_title = self.args.get("grant_title", "")
        deadline = self.args.get("deadline", "")
        status = self.args.get("status", "")

        await self.agent.context.log.log(
            type="tool",
            heading=f"📊 Grant Tracking: {action}",
            content=f"Grant: {grant_title or 'All'}",
        )

        try:
            coordinator = GrantCoordinator()

            if action == "add":
                if not grant_title or not deadline:
                    return Response(
                        message="Error: grant_title and deadline required for add",
                        break_loop=False
                    )

                # Add grant to tracking
                tracking_data = {
                    'title': grant_title,
                    'deadline': deadline,
                    'status': 'in_progress',
                    'added_date': datetime.now().isoformat()
                }

                coordinator.add_to_tracking(tracking_data)
                result = f"Added {grant_title} to tracking system.\nDeadline: {deadline}"

            elif action == "deadlines":
                # Get upcoming deadlines
                tracked_grants = coordinator.get_tracked_grants()

                # Sort by deadline
                upcoming = []
                for grant in tracked_grants:
                    try:
                        deadline_date = datetime.fromisoformat(grant['deadline'])
                        days_until = (deadline_date - datetime.now()).days

                        if days_until >= 0:
                            upcoming.append({
                                **grant,
                                'days_until': days_until
                            })
                    except:
                        pass

                upcoming.sort(key=lambda x: x['days_until'])

                if upcoming:
                    result = "## Upcoming Grant Deadlines\n\n"
                    for grant in upcoming[:10]:
                        urgency = "🔴 URGENT" if grant['days_until'] < 7 else "🟡" if grant['days_until'] < 30 else "🟢"
                        result += f"{urgency} **{grant['title']}**\n"
                        result += f"   Deadline: {grant['deadline']} ({grant['days_until']} days)\n"
                        result += f"   Status: {grant.get('status', 'unknown')}\n\n"
                else:
                    result = "No upcoming grant deadlines."

            elif action == "update":
                if not grant_title or not status:
                    return Response(
                        message="Error: grant_title and status required for update",
                        break_loop=False
                    )

                coordinator.update_grant_status(grant_title, status)
                result = f"Updated {grant_title} status to: {status}"

            else:  # status
                tracked_grants = coordinator.get_tracked_grants()

                if tracked_grants:
                    result = "## Grant Application Status\n\n"
                    status_groups = {}

                    for grant in tracked_grants:
                        status = grant.get('status', 'unknown')
                        if status not in status_groups:
                            status_groups[status] = []
                        status_groups[status].append(grant)

                    for status, grants in status_groups.items():
                        result += f"### {status.upper()} ({len(grants)})\n"
                        for grant in grants:
                            result += f"- {grant['title']}\n"
                        result += "\n"
                else:
                    result = "No grants currently tracked."

            return Response(message=result, break_loop=False)

        except Exception as e:
            error_msg = f"Grant tracking error: {str(e)}"
            await self.agent.context.log.log(
                type="error",
                heading="Grant Tracking Failed",
                content=error_msg,
            )
            return Response(message=error_msg, break_loop=False)
