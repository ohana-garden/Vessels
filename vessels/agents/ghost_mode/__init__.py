"""
Ghost Mode for safe agent deployment.

Allows agents to observe real queries and propose actions without
executing them, enabling safety verification before production deployment.
"""

from vessels.agents.ghost_mode.ghost_agent import GhostAgent, SimulationEntry
from vessels.agents.ghost_mode.safety_report import SafetyReport, SafetyReportGenerator

__all__ = [
    "GhostAgent",
    "SimulationEntry",
    "SafetyReport",
    "SafetyReportGenerator",
]
