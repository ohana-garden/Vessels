"""
Shoghi Moral Geometry - Tool Execution Gating
Checks if tool execution is morally permissible before execution
"""
from python.helpers.extension import Extension
from python.helpers.errors import ClaudeCodeException


class ShoghiMoralGate(Extension):
    """Gate tool execution through Shoghi moral constraints"""

    async def execute(self, **kwargs):
        """
        Check if tool execution is morally permissible

        If the tool execution would violate moral constraints:
        - Block the execution
        - Log the violation
        - Suggest alternative approach
        """

        tool = kwargs.get('tool')
        if not tool:
            return

        # Skip gating if Shoghi not initialized
        if not hasattr(self.agent, 'shoghi_gate'):
            return

        # Extract action context from tool
        action_context = {
            'tool_name': tool.name,
            'tool_args': tool.args,
            'agent_name': self.agent.agent_name,
            'agent_number': self.agent.number
        }

        # Check with moral gate
        gate_result = self.agent.shoghi_gate.check_action(action_context)

        if not gate_result.get('permitted', True):
            # Action blocked by moral constraints
            violation = gate_result.get('violation', 'Unknown violation')
            suggestion = gate_result.get('suggestion', 'Reconsider your approach')

            # Log the blocked action
            self.agent.context.log.log(
                type="warning",
                heading=f"⚠️ Moral Constraint Violation",
                content=f"Action blocked: {violation}\n\nSuggestion: {suggestion}",
                finished=True,
            )

            # Raise exception to prevent execution
            raise ClaudeCodeException(
                message=f"Moral constraint violation: {violation}",
                suggestion=suggestion
            )

        # If permitted, log the check (optional, can be disabled for performance)
        if gate_result.get('warnings'):
            self.agent.context.log.log(
                type="info",
                heading=f"🌺 Moral Check",
                content=f"Action permitted with caution: {gate_result.get('warnings')}",
                finished=True,
            )
