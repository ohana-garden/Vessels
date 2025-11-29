"""
Built-in SSFs for Vessels.

This module provides a comprehensive library of pre-built SSFs covering
common coordination and operational needs:

- communication/: SMS, email, notifications
- data/: Graphiti queries, memory operations
- scheduling/: Appointments, reminders
- coordination/: A2A delegation, agent spawning
- computation/: Data transformation, validation
- external/: MCP tool wrappers, HTTP requests
"""

from typing import Dict, List
from uuid import UUID

from ..schema import SSFDefinition
from ..registry import SSFRegistry


async def register_all_builtins(registry: SSFRegistry) -> List[UUID]:
    """
    Register all built-in SSFs with a registry.

    Args:
        registry: SSF registry to register with

    Returns:
        List of registered SSF IDs
    """
    registered_ids = []

    # Import and register from each category
    from . import communication
    from . import data
    from . import scheduling
    from . import coordination
    from . import computation
    from . import external

    categories = [
        communication,
        data,
        scheduling,
        coordination,
        computation,
        external,
    ]

    for category_module in categories:
        if hasattr(category_module, 'get_builtin_ssfs'):
            ssfs = category_module.get_builtin_ssfs()
            for ssf in ssfs:
                ssf_id = await registry.register(ssf)
                registered_ids.append(ssf_id)

    return registered_ids


def get_builtin_ssf_summary() -> Dict[str, int]:
    """Get a summary of available built-in SSFs by category."""
    from . import communication
    from . import data
    from . import scheduling
    from . import coordination
    from . import computation
    from . import external

    summary = {}
    categories = {
        "communication": communication,
        "data": data,
        "scheduling": scheduling,
        "coordination": coordination,
        "computation": computation,
        "external": external,
    }

    for name, module in categories.items():
        if hasattr(module, 'get_builtin_ssfs'):
            summary[name] = len(module.get_builtin_ssfs())
        else:
            summary[name] = 0

    return summary
