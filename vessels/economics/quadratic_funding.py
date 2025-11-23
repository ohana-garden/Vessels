"""
Quadratic Funding implementation for democratic capital allocation.

QF amplifies the preferences of many over the few, aligning capital
allocation with community consensus.

Formula: match = (sum(sqrt(individual_contributions)))^2

Example:
  Project A: 10 people × $1 = $10 total → match weight = (10 × √1)² = 100
  Project B: 1 person × $10 = $10 total → match weight = (1 × √10)² ≈ 10

Project A receives 10× more matching funds despite same total contributions!
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from math import sqrt
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Project:
    """
    Project eligible for quadratic funding.

    Represents a community initiative seeking funding.
    """
    id: str
    name: str
    description: str
    owner_id: str
    kala_contributions: Dict[str, float] = field(default_factory=dict)  # contributor_id → amount
    total_contributed: float = 0.0
    matching_funds_allocated: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "active"  # active, completed, cancelled

    def add_contribution(self, contributor_id: str, amount: float) -> None:
        """
        Record a contribution to this project.

        Args:
            contributor_id: ID of contributor
            amount: Kala amount contributed
        """
        if contributor_id in self.kala_contributions:
            self.kala_contributions[contributor_id] += amount
        else:
            self.kala_contributions[contributor_id] = amount

        self.total_contributed += amount

    def get_contributor_count(self) -> int:
        """Get number of unique contributors."""
        return len(self.kala_contributions)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "total_contributed": self.total_contributed,
            "matching_funds_allocated": self.matching_funds_allocated,
            "contributor_count": self.get_contributor_count(),
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }


class QuadraticFundingAllocator:
    """
    Allocates matching funds using quadratic funding formula.

    Quadratic funding provides democratic capital allocation by
    amplifying the signal of community consensus vs. individual
    whale contributions.

    This aligns with the Unity virtue by giving voice to the many.
    """

    def __init__(self, prevent_sybil: bool = True):
        """
        Initialize QF allocator.

        Args:
            prevent_sybil: Enable Sybil attack prevention measures
        """
        self.prevent_sybil = prevent_sybil
        self.allocation_history: List[Dict] = []

    def calculate_match_weight(self, project: Project) -> float:
        """
        Calculate quadratic funding match weight for a project.

        Formula: (sum(sqrt(individual_contributions)))^2

        Args:
            project: Project to calculate weight for

        Returns:
            Match weight (higher = more matching funds)
        """
        if not project.kala_contributions:
            return 0.0

        # Sum of square roots
        sqrt_sum = sum(sqrt(amount) for amount in project.kala_contributions.values())

        # Square the sum
        match_weight = sqrt_sum ** 2

        return match_weight

    def allocate(
        self,
        projects: List[Project],
        matching_pool: float
    ) -> Dict[str, float]:
        """
        Allocate matching pool across projects using QF.

        Args:
            projects: List of projects to fund
            matching_pool: Total Kala available for matching

        Returns:
            Dictionary of project_id → allocated_kala
        """
        if not projects:
            logger.warning("No projects to allocate funds to")
            return {}

        if matching_pool <= 0:
            logger.warning(f"Invalid matching pool: {matching_pool}")
            return {}

        # Calculate match weights for each project
        match_weights = {}
        total_match_weight = 0.0

        for project in projects:
            if project.status != "active":
                continue  # Skip non-active projects

            weight = self.calculate_match_weight(project)

            # Sybil prevention: cap individual contributions
            if self.prevent_sybil:
                weight = self._apply_sybil_prevention(project, weight)

            match_weights[project.id] = weight
            total_match_weight += weight

        if total_match_weight == 0:
            logger.warning("Total match weight is 0, no allocations made")
            return {}

        # Normalize to matching pool
        allocations = {
            project_id: (weight / total_match_weight) * matching_pool
            for project_id, weight in match_weights.items()
        }

        # Update project records
        for project in projects:
            if project.id in allocations:
                project.matching_funds_allocated = allocations[project.id]

        # Record allocation
        self.allocation_history.append({
            "timestamp": datetime.now().isoformat(),
            "matching_pool": matching_pool,
            "projects_count": len(allocations),
            "allocations": allocations
        })

        logger.info(
            f"QF Allocation complete: {matching_pool} kala distributed across "
            f"{len(allocations)} projects"
        )

        return allocations

    def _apply_sybil_prevention(self, project: Project, base_weight: float) -> float:
        """
        Apply Sybil attack prevention measures.

        Caps the influence of large individual contributions to
        prevent gaming through fake identities.

        Args:
            project: Project to check
            base_weight: Calculated match weight

        Returns:
            Adjusted match weight
        """
        # Simple heuristic: cap individual contributions at 20% of total
        max_individual_ratio = 0.2

        for contributor_id, amount in project.kala_contributions.items():
            if project.total_contributed > 0:
                ratio = amount / project.total_contributed
                if ratio > max_individual_ratio:
                    # Large individual contribution detected - apply penalty
                    penalty_factor = max_individual_ratio / ratio
                    adjusted_weight = base_weight * penalty_factor

                    logger.warning(
                        f"Sybil prevention: Project {project.id} has large individual "
                        f"contribution ({ratio:.1%}), applying penalty ({penalty_factor:.2f})"
                    )

                    return adjusted_weight

        return base_weight

    def get_allocation_summary(
        self,
        projects: List[Project],
        allocations: Dict[str, float]
    ) -> str:
        """
        Generate human-readable allocation summary.

        Args:
            projects: List of projects
            allocations: Allocation results

        Returns:
            Formatted summary string
        """
        summary = "QUADRATIC FUNDING ALLOCATION SUMMARY\n"
        summary += "=" * 50 + "\n\n"

        project_dict = {p.id: p for p in projects}

        # Sort by allocation (highest first)
        sorted_allocations = sorted(
            allocations.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for project_id, allocated_amount in sorted_allocations:
            project = project_dict.get(project_id)
            if not project:
                continue

            summary += f"Project: {project.name}\n"
            summary += f"  Direct Contributions: {project.total_contributed:.2f} kala "
            summary += f"({project.get_contributor_count()} contributors)\n"
            summary += f"  Matching Funds: {allocated_amount:.2f} kala\n"
            summary += f"  Total Funding: {project.total_contributed + allocated_amount:.2f} kala\n"
            summary += "\n"

        total_matched = sum(allocations.values())
        summary += f"Total Matching Pool Distributed: {total_matched:.2f} kala\n"

        return summary
