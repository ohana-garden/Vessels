"""
Ghost Agent wrapper for simulation mode.

Allows agents to run in "ghost mode" where they observe queries and
propose actions but don't execute them. Useful for safety testing
before production deployment.

REQUIRES AgentZeroCore - all ghost operations are coordinated through A0.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional, TYPE_CHECKING
from datetime import datetime
import json

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore

logger = logging.getLogger(__name__)


@dataclass
class SimulationEntry:
    """Record of a simulated agent action."""
    query: Any
    proposed_action: Any
    gating_result: Any
    measured_state: Any
    timestamp: datetime
    would_be_blocked: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": str(self.query),
            "proposed_action": str(self.proposed_action),
            "would_be_blocked": self.would_be_blocked,
            "violations": self.violations,
            "measured_state": str(self.measured_state),
            "timestamp": self.timestamp.isoformat()
        }


class GhostAgent:
    """
    Wrapper for agents in simulation mode.

    Ghost agents observe real queries, generate proposed actions,
    and simulate the gating process WITHOUT actually executing
    the actions. This allows:

    1. Safety verification before production deployment
    2. Testing new agent classes against real queries
    3. Analyzing gating patterns without risk
    4. Building confidence in agent behavior

    Usage:
        # Wrap agent in ghost mode
        ghost = GhostAgent(my_agent, action_gate)

        # Observe queries for N days
        for query in daily_queries:
            ghost.handle_query(query)

        # Review safety report
        report = ghost.generate_safety_report()
        if report.is_safe():
            # Deploy to production
            my_agent.deploy()
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        agent: Any,
        action_gate: Any = None,
        ghost_mode: bool = True,
        log_file: Optional[str] = None
    ):
        """
        Initialize Ghost Agent.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            agent: Agent to wrap in ghost mode
            action_gate: ActionGate for validation (defaults to A0's gate)
            ghost_mode: If True, actions are simulated (not executed)
            log_file: Optional file to log simulation entries
        """
        if agent_zero is None:
            raise ValueError("GhostAgent requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.agent = agent
        self.action_gate = action_gate or agent_zero.gate
        self.ghost_mode = ghost_mode
        self.log_file = log_file
        self.simulation_log: List[SimulationEntry] = []

        # Register with A0
        self.agent_zero.ghost_agent = self

        logger.info(
            f"Ghost Agent initialized for {agent.__class__.__name__} "
            f"(ghost_mode={ghost_mode}) with A0"
        )

    def handle_query(self, query: Any, query_metadata: Optional[Dict] = None) -> Optional[Any]:
        """
        Handle a query in ghost mode.

        Args:
            query: User query
            query_metadata: Optional metadata about the query

        Returns:
            None in ghost mode, actual result in normal mode
        """
        # Agent generates action
        try:
            proposed_action = self.agent.generate_action(query)
        except Exception as e:
            logger.error(f"Agent failed to generate action: {e}")
            # Log failure
            entry = SimulationEntry(
                query=query,
                proposed_action=None,
                gating_result=None,
                measured_state=None,
                timestamp=datetime.now(),
                would_be_blocked=True,
                violations=[f"Action generation failed: {str(e)}"]
            )
            self.simulation_log.append(entry)
            self._write_to_log(entry)
            return None

        if self.ghost_mode:
            # Dry-run gating (don't execute)
            gating_result = self._dry_run_gate(proposed_action)

            # Log simulation entry
            entry = SimulationEntry(
                query=query,
                proposed_action=proposed_action,
                gating_result=gating_result,
                measured_state=gating_result.measured_state if gating_result else None,
                timestamp=datetime.now(),
                would_be_blocked=not gating_result.allowed if gating_result else True,
                violations=[str(v) for v in getattr(gating_result, 'violations', [])]
            )

            self.simulation_log.append(entry)
            self._write_to_log(entry)

            # Don't execute action!
            logger.debug(
                f"Ghost mode: Would {'allow' if gating_result.allowed else 'block'} action for query"
            )

            return None

        else:
            # Normal execution mode
            return self.agent.execute_action(proposed_action)

    def _dry_run_gate(self, proposed_action: Any) -> Any:
        """
        Perform dry-run gating (measure state but don't intervene).

        Args:
            proposed_action: Action to gate

        Returns:
            GatingResult with dry_run flag set
        """
        # Check if action_gate supports dry_run parameter
        try:
            # Try with dry_run parameter
            result = self.action_gate.gate_action(
                agent_id=getattr(self.agent, 'agent_id', 'ghost_agent'),
                action=proposed_action,
                action_metadata={"ghost_mode": True},
                dry_run=True
            )
            return result
        except TypeError:
            # action_gate doesn't support dry_run, call normally
            # but note that this won't prevent actual intervention
            logger.warning("ActionGate doesn't support dry_run mode")
            result = self.action_gate.gate_action(
                agent_id=getattr(self.agent, 'agent_id', 'ghost_agent'),
                action=proposed_action,
                action_metadata={"ghost_mode": True}
            )
            return result

    def _write_to_log(self, entry: SimulationEntry) -> None:
        """Write simulation entry to log file."""
        if not self.log_file:
            return

        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")

    def generate_safety_report(self) -> 'SafetyReport':
        """
        Generate safety report from simulation log.

        Returns:
            SafetyReport with analysis of agent behavior
        """
        from vessels.agents.ghost_mode.safety_report import SafetyReportGenerator

        generator = SafetyReportGenerator(self.simulation_log)
        return generator.generate()

    def clear_log(self) -> None:
        """Clear simulation log."""
        self.simulation_log = []
        logger.info("Ghost agent simulation log cleared")

    def export_log(self, filepath: str) -> None:
        """
        Export simulation log to file.

        Args:
            filepath: Path to export JSON log
        """
        with open(filepath, 'w') as f:
            json.dump(
                [entry.to_dict() for entry in self.simulation_log],
                f,
                indent=2
            )

        logger.info(f"Exported {len(self.simulation_log)} simulation entries to {filepath}")

    def __repr__(self) -> str:
        return (
            f"GhostAgent(agent={self.agent.__class__.__name__}, "
            f"ghost_mode={self.ghost_mode}, "
            f"simulations={len(self.simulation_log)})"
        )
