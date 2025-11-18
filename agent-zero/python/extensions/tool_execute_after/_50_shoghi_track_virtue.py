"""
Shoghi Moral Geometry - Post-Action Tracking
Tracks virtue state changes after tool execution
"""
from python.helpers.extension import Extension


class ShoghiTrackVirtue(Extension):
    """Track virtue state changes after tool execution"""

    async def execute(self, **kwargs):
        """
        Update virtue state based on action results

        Analyzes:
        - Tool success/failure
        - Impact of the action
        - Virtue development
        """

        tool = kwargs.get('tool')
        result = kwargs.get('result')

        if not tool or not result:
            return

        # Skip if Shoghi not initialized
        if not hasattr(self.agent, 'shoghi_tracker'):
            return

        # Analyze action outcome
        action_outcome = {
            'tool_name': tool.name,
            'success': not isinstance(result, Exception),
            'result_summary': str(result)[:200] if result else None
        }

        # Update virtue state based on action
        self.agent.shoghi_tracker.record_action(
            action=tool.name,
            outcome=action_outcome,
            context={'agent': self.agent.agent_name}
        )

        # Check for virtue state alerts (e.g., low virtues that need attention)
        current_state = self.agent.shoghi_tracker.get_current_state()
        low_virtues = {k: v for k, v in current_state.items() if v < 0.4}

        if low_virtues:
            virtue_list = ', '.join([f"{k}: {v:.2f}" for k, v in low_virtues.items()])
            self.agent.context.log.log(
                type="warning",
                heading=f"⚠️ Low Virtue Alert",
                content=f"Attention needed: {virtue_list}",
                finished=True,
            )
