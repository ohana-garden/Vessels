"""
Economic coordination modules for Vessels platform.

Includes:
- Quadratic Funding for democratic capital allocation
- Inter-Community Clearing for cross-community exchanges
- Project tracking and governance
"""

from vessels.economics.quadratic_funding import QuadraticFundingAllocator, Project
from vessels.economics.clearing_house import InterCommunityClearingHouse, SwapProposal, Offer
from vessels.economics.projects import ProjectTracker, ProjectStatus

__all__ = [
    "QuadraticFundingAllocator",
    "Project",
    "InterCommunityClearingHouse",
    "SwapProposal",
    "Offer",
    "ProjectTracker",
    "ProjectStatus",
]
