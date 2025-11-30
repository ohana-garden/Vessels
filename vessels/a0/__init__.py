"""
A0 Integration Module for Vessels SSF System.

This module integrates SSF execution with Agent Zero's reasoning loop,
replacing A0's default code execution with constrained SSF invocation.

The key principle: agents can ONLY affect the world through SSFs.
There is no raw code execution, no direct API calls, no escape hatch.
"""

from .ssf_integration import (
    A0SSFIntegration,
    ToolDefinition,
    ToolResult,
)

__all__ = [
    "A0SSFIntegration",
    "ToolDefinition",
    "ToolResult",
]
