"""
Grants Use Case - Main orchestration for vessel-based grant management.

This module provides the primary interface for grant operations within a Vessel context.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .models import (
    GrantApplication,
    GrantOpportunity,
    GrantSearchCriteria,
    GrantStatus,
)
from .repository import GrantRepository
from .discovery import GrantDiscoveryService
from .writer import GrantApplicationWriter

if TYPE_CHECKING:
    from vessels.core import Vessel

logger = logging.getLogger(__name__)


class GrantsUseCase:
    """
    Grants Use Case - Vessel-integrated grant management.

    This class provides the main interface for:
    - Discovering grant opportunities
    - Creating and managing applications
    - Tracking grant pipeline
    - Generating reports

    All operations are scoped to a specific Vessel, ensuring:
    - Data isolation between vessels
    - Action gating enforcement (if configured)
    - Proper measurement tracking

    Example:
        >>> from vessels.core import VesselRegistry
        >>> from vessels.use_cases.grants import GrantsUseCase
        >>>
        >>> registry = VesselRegistry()
        >>> vessel = registry.create_vessel("Elder Care", "lower_puna")
        >>>
        >>> grants = GrantsUseCase(vessel)
        >>> opportunities = grants.discover_grants(focus_areas=["elder care"])
        >>> for grant in opportunities[:3]:
        ...     print(f"{grant.title}: {grant.amount}")
    """

    def __init__(
        self,
        vessel: "Vessel",
        applicant_info: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize grants use case for a vessel.

        Args:
            vessel: The Vessel context for grant operations
            applicant_info: Information about the applicant organization.
                If not provided, defaults will be generated from vessel info.
        """
        self.vessel = vessel
        self.vessel_id = vessel.vessel_id

        # Initialize components
        self.repository = GrantRepository(vessel_id=self.vessel_id)
        self.discovery = GrantDiscoveryService(vessel_id=self.vessel_id)

        # Build applicant info from vessel or use provided
        self.applicant_info = applicant_info or self._build_applicant_info()
        self.writer = GrantApplicationWriter(
            vessel_id=self.vessel_id,
            applicant_info=self.applicant_info
        )

        logger.info(f"Initialized GrantsUseCase for vessel {self.vessel_id}")

    def _build_applicant_info(self) -> Dict[str, Any]:
        """Build applicant info from vessel context."""
        return {
            "organization_name": self.vessel.name,
            "community": ", ".join(self.vessel.community_ids),
            "mission": self.vessel.description or "serving our community",
            "vessel_id": self.vessel_id,
        }

    # Discovery Operations

    def discover_grants(
        self,
        focus_areas: Optional[List[str]] = None,
        geographic_scope: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        sources: Optional[List[str]] = None,
        save_results: bool = True
    ) -> List[GrantOpportunity]:
        """
        Discover grant opportunities matching criteria.

        Args:
            focus_areas: Areas to focus on (e.g., ["elder care", "healthcare"])
            geographic_scope: Geographic area (e.g., "Hawaii")
            min_amount: Minimum grant amount
            max_amount: Maximum grant amount
            sources: Specific sources to search
            save_results: Whether to save discovered grants to repository

        Returns:
            List of discovered GrantOpportunity objects, sorted by match score
        """
        # Build search criteria
        criteria = GrantSearchCriteria(
            focus_areas=focus_areas or [],
            min_amount=min_amount,
            max_amount=max_amount,
            geographic_scope=geographic_scope,
        )

        # Discover grants
        grants = self.discovery.discover_grants(criteria, sources=sources)

        # Save to repository if requested
        if save_results:
            for grant in grants:
                self.repository.save_grant(grant)
            logger.info(f"Saved {len(grants)} grants to repository")

        return grants

    def get_grant(self, grant_id: str) -> Optional[GrantOpportunity]:
        """
        Get a specific grant by ID.

        Args:
            grant_id: The grant ID

        Returns:
            The grant if found, None otherwise
        """
        return self.repository.get_grant(grant_id)

    def list_grants(
        self,
        status: Optional[GrantStatus] = None,
        limit: int = 100
    ) -> List[GrantOpportunity]:
        """
        List grants for this vessel.

        Args:
            status: Optional status filter
            limit: Maximum number to return

        Returns:
            List of grants
        """
        return self.repository.list_grants(status=status, limit=limit)

    def search_grants(
        self,
        criteria: GrantSearchCriteria
    ) -> List[GrantOpportunity]:
        """
        Search grants by criteria.

        Args:
            criteria: Search criteria

        Returns:
            Matching grants
        """
        return self.repository.search_grants(criteria)

    def analyze_grant(self, grant_id: str) -> Optional[Dict[str, Any]]:
        """
        Perform detailed analysis of a grant.

        Args:
            grant_id: The grant ID

        Returns:
            Analysis results or None if not found
        """
        grant = self.repository.get_grant(grant_id)
        if not grant:
            return None

        analysis = self.discovery.analyze_grant(grant)

        # Update grant status to analyzed
        self.repository.update_grant_status(grant_id, GrantStatus.ANALYZING)

        return analysis

    # Application Operations

    def create_application(
        self,
        grant_id: str,
        custom_sections: Optional[Dict[str, str]] = None
    ) -> Optional[GrantApplication]:
        """
        Create a new application for a grant.

        Args:
            grant_id: The grant to apply for
            custom_sections: Optional custom narrative sections

        Returns:
            The created application or None if grant not found
        """
        grant = self.repository.get_grant(grant_id)
        if not grant:
            logger.warning(f"Grant {grant_id} not found")
            return None

        # Check if application already exists
        existing = self.repository.get_application_for_grant(grant_id)
        if existing:
            logger.info(f"Application already exists for grant {grant_id}")
            return existing

        # Create application
        application = self.writer.create_application(grant, custom_sections)

        # Save to repository
        self.repository.save_application(application)

        # Update grant status
        self.repository.update_grant_status(grant_id, GrantStatus.APPLICATION_DRAFT)

        return application

    def get_application(self, application_id: str) -> Optional[GrantApplication]:
        """
        Get an application by ID.

        Args:
            application_id: The application ID

        Returns:
            The application if found
        """
        return self.repository.get_application(application_id)

    def list_applications(
        self,
        status: Optional[GrantStatus] = None
    ) -> List[GrantApplication]:
        """
        List applications for this vessel.

        Args:
            status: Optional status filter

        Returns:
            List of applications
        """
        return self.repository.list_applications(status=status)

    def update_application_section(
        self,
        application_id: str,
        section_name: str,
        content: str
    ) -> Optional[GrantApplication]:
        """
        Update a section of an application.

        Args:
            application_id: The application ID
            section_name: Name of the section to update
            content: New content

        Returns:
            Updated application or None if not found
        """
        application = self.repository.get_application(application_id)
        if not application:
            return None

        application = self.writer.update_section(application, section_name, content)
        self.repository.save_application(application)

        return application

    def finalize_application(self, application_id: str) -> Optional[GrantApplication]:
        """
        Finalize an application for submission.

        Args:
            application_id: The application ID

        Returns:
            Finalized application or None if not found
        """
        application = self.repository.get_application(application_id)
        if not application:
            return None

        application = self.writer.finalize_application(application)
        self.repository.save_application(application)

        # Update grant status
        self.repository.update_grant_status(
            application.grant_id,
            GrantStatus.READY_TO_APPLY
        )

        return application

    def submit_application(self, application_id: str) -> Optional[GrantApplication]:
        """
        Mark an application as submitted.

        Args:
            application_id: The application ID

        Returns:
            Updated application or None if not found
        """
        application = self.repository.get_application(application_id)
        if not application:
            return None

        application.status = GrantStatus.SUBMITTED
        application.submission_date = datetime.utcnow()
        application.updated_at = datetime.utcnow()

        self.repository.save_application(application)
        self.repository.update_grant_status(
            application.grant_id,
            GrantStatus.SUBMITTED
        )

        logger.info(f"Application {application_id} submitted")
        return application

    # Reporting Operations

    def get_pipeline_summary(self) -> Dict[str, Any]:
        """
        Get summary of the grant pipeline.

        Returns:
            Summary statistics and status breakdown
        """
        all_grants = self.repository.list_grants(limit=1000)
        all_applications = self.repository.list_applications(limit=1000)

        # Count by status
        grant_status_counts = {}
        for grant in all_grants:
            status = grant.status.value
            grant_status_counts[status] = grant_status_counts.get(status, 0) + 1

        app_status_counts = {}
        for app in all_applications:
            status = app.status.value
            app_status_counts[status] = app_status_counts.get(status, 0) + 1

        # Upcoming deadlines
        now = datetime.utcnow()
        upcoming = [
            g for g in all_grants
            if g.deadline > now and g.status not in [GrantStatus.SUBMITTED, GrantStatus.AWARDED, GrantStatus.REJECTED]
        ]
        upcoming.sort(key=lambda g: g.deadline)

        return {
            "vessel_id": self.vessel_id,
            "summary_date": now.isoformat(),
            "grants": {
                "total": len(all_grants),
                "by_status": grant_status_counts,
            },
            "applications": {
                "total": len(all_applications),
                "by_status": app_status_counts,
            },
            "upcoming_deadlines": [
                {
                    "id": g.id,
                    "title": g.title,
                    "deadline": g.deadline.isoformat(),
                    "days_remaining": (g.deadline - now).days,
                }
                for g in upcoming[:5]
            ],
            "high_match_opportunities": [
                {
                    "id": g.id,
                    "title": g.title,
                    "score": g.analysis_score,
                    "amount": g.amount,
                }
                for g in sorted(all_grants, key=lambda x: x.analysis_score, reverse=True)[:5]
            ],
        }

    def close(self) -> None:
        """Close connections and clean up resources."""
        self.repository.close()
