"""
Grant Discovery Service

Discovers and analyzes grant opportunities from various sources.
"""

import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from .models import GrantOpportunity, GrantSearchCriteria, GrantStatus

logger = logging.getLogger(__name__)

# Configuration constants
REQUEST_TIMEOUT = 30
DEFAULT_USER_AGENT = "Vessels Grant Discovery Bot/1.0"


class GrantDiscoveryService:
    """
    Service for discovering grants from various sources.

    Searches grant databases and websites to find opportunities
    matching the vessel's focus areas and eligibility.
    """

    def __init__(self, vessel_id: str):
        """
        Initialize discovery service for a vessel.

        Args:
            vessel_id: The vessel ID for context
        """
        self.vessel_id = vessel_id
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": DEFAULT_USER_AGENT,
        })

    def discover_grants(
        self,
        criteria: GrantSearchCriteria,
        sources: Optional[List[str]] = None
    ) -> List[GrantOpportunity]:
        """
        Discover grants matching criteria from configured sources.

        Args:
            criteria: Search criteria
            sources: Optional list of source names to search (defaults to all)

        Returns:
            List of discovered grant opportunities
        """
        grants: List[GrantOpportunity] = []

        # Default sources
        all_sources = sources or ["grants_gov", "hcf", "elder_care"]

        for source in all_sources:
            try:
                if source == "grants_gov":
                    grants.extend(self._search_grants_gov(criteria))
                elif source == "hcf":
                    grants.extend(self._search_hcf_grants(criteria))
                elif source == "elder_care":
                    grants.extend(self._search_elder_care_grants(criteria))
                else:
                    logger.warning(f"Unknown grant source: {source}")
            except requests.RequestException as e:
                logger.error(f"Network error searching {source}: {e}")
            except ValueError as e:
                logger.error(f"Data error searching {source}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error searching {source}: {e}", exc_info=True)

        # Score and sort grants
        for grant in grants:
            grant.analysis_score = self._calculate_match_score(grant, criteria)
            grant.match_reasoning = self._generate_match_reasoning(grant, criteria)
            grant.vessel_id = self.vessel_id

        # Sort by score descending
        grants.sort(key=lambda g: g.analysis_score, reverse=True)

        logger.info(f"Discovered {len(grants)} grants for vessel {self.vessel_id}")
        return grants

    def _search_grants_gov(self, criteria: GrantSearchCriteria) -> List[GrantOpportunity]:
        """
        Search Grants.gov for opportunities.

        In production, this would use the Grants.gov API.
        For now, returns sample data matching criteria.
        """
        # This is a placeholder - in production, use actual Grants.gov API
        # https://www.grants.gov/web/grants/search-grants.html
        logger.info("Searching Grants.gov (placeholder implementation)")

        grants = []

        # Generate sample grants based on criteria
        if any(fa.lower() in ["healthcare", "elder care", "aging"] for fa in criteria.focus_areas):
            grants.append(GrantOpportunity(
                id=f"grants-gov-{uuid.uuid4().hex[:8]}",
                title="HHS Elder Care Innovation Grant",
                description="Federal funding for innovative elder care programs that improve "
                           "health outcomes and reduce hospitalization rates.",
                funder="U.S. Department of Health and Human Services",
                amount="$100,000 - $500,000",
                deadline=datetime.utcnow() + timedelta(days=90),
                eligibility=["501(c)(3) nonprofit", "State or local government", "Tribal organization"],
                focus_areas=["elder care", "healthcare", "community health"],
                geographic_scope="National",
                application_url="https://www.grants.gov/",
                contact_info={"email": "grants@hhs.gov"},
                requirements=["Narrative (max 25 pages)", "Budget justification", "Letters of support"],
                status=GrantStatus.DISCOVERED,
                discovery_date=datetime.utcnow(),
            ))

        if any(fa.lower() in ["technology", "digital", "innovation"] for fa in criteria.focus_areas):
            grants.append(GrantOpportunity(
                id=f"grants-gov-{uuid.uuid4().hex[:8]}",
                title="NSF Community Technology Grant",
                description="Support for community organizations implementing technology "
                           "solutions for underserved populations.",
                funder="National Science Foundation",
                amount="$50,000 - $250,000",
                deadline=datetime.utcnow() + timedelta(days=120),
                eligibility=["Nonprofit organization", "Educational institution"],
                focus_areas=["technology", "digital inclusion", "community development"],
                geographic_scope="National",
                application_url="https://www.nsf.gov/funding/",
                contact_info={"email": "info@nsf.gov"},
                requirements=["Project narrative", "Data management plan", "Budget"],
                status=GrantStatus.DISCOVERED,
                discovery_date=datetime.utcnow(),
            ))

        return grants

    def _search_hcf_grants(self, criteria: GrantSearchCriteria) -> List[GrantOpportunity]:
        """
        Search Hawaii Community Foundation grants.

        In production, this would scrape/query HCF's grant database.
        """
        logger.info("Searching Hawaii Community Foundation (placeholder implementation)")

        grants = []

        # Sample Hawaii-focused grants
        if criteria.geographic_scope and "hawaii" in criteria.geographic_scope.lower():
            grants.append(GrantOpportunity(
                id=f"hcf-{uuid.uuid4().hex[:8]}",
                title="Hawaii Community Health Initiative",
                description="Supporting community-based health programs across the Hawaiian islands, "
                           "with priority for rural and underserved communities.",
                funder="Hawaii Community Foundation",
                amount="$25,000 - $100,000",
                deadline=datetime.utcnow() + timedelta(days=60),
                eligibility=["Hawaii-based 501(c)(3)", "Fiscal sponsor available"],
                focus_areas=["community health", "elder care", "cultural preservation"],
                geographic_scope="Hawaii",
                application_url="https://hawaiicommunityfoundation.org/",
                contact_info={"email": "grants@hcf-hawaii.org"},
                requirements=["Online application", "Organizational budget", "Board list"],
                status=GrantStatus.DISCOVERED,
                discovery_date=datetime.utcnow(),
            ))

            grants.append(GrantOpportunity(
                id=f"hcf-{uuid.uuid4().hex[:8]}",
                title="Kupuna Care Program Fund",
                description="Dedicated funding for programs serving Hawaii's kupuna (elders), "
                           "including meals, transportation, and social services.",
                funder="Hawaii Community Foundation - Kupuna Fund",
                amount="$10,000 - $50,000",
                deadline=datetime.utcnow() + timedelta(days=45),
                eligibility=["Hawaii nonprofit", "Elder-serving organization"],
                focus_areas=["elder care", "kupuna services", "senior programs"],
                geographic_scope="Hawaii",
                application_url="https://hawaiicommunityfoundation.org/kupuna",
                contact_info={"email": "kupuna@hcf-hawaii.org"},
                requirements=["Service description", "Elder count served", "Budget"],
                status=GrantStatus.DISCOVERED,
                discovery_date=datetime.utcnow(),
            ))

        return grants

    def _search_elder_care_grants(self, criteria: GrantSearchCriteria) -> List[GrantOpportunity]:
        """
        Search elder care specific grant sources.
        """
        logger.info("Searching elder care grants (placeholder implementation)")

        grants = []

        if any(fa.lower() in ["elder care", "aging", "senior", "kupuna"] for fa in criteria.focus_areas):
            grants.append(GrantOpportunity(
                id=f"aoa-{uuid.uuid4().hex[:8]}",
                title="Administration on Aging Community Grant",
                description="Federal funding through the Older Americans Act for community-based "
                           "services supporting older adults to live independently.",
                funder="Administration for Community Living",
                amount="$75,000 - $300,000",
                deadline=datetime.utcnow() + timedelta(days=75),
                eligibility=["Area Agency on Aging", "Tribal organization", "Nonprofit partner"],
                focus_areas=["elder care", "independent living", "caregiver support"],
                geographic_scope="National",
                application_url="https://acl.gov/grants",
                contact_info={"email": "aclinfo@acl.hhs.gov"},
                requirements=["Program design", "Outcome measures", "Sustainability plan"],
                status=GrantStatus.DISCOVERED,
                discovery_date=datetime.utcnow(),
            ))

        return grants

    def _calculate_match_score(
        self,
        grant: GrantOpportunity,
        criteria: GrantSearchCriteria
    ) -> float:
        """
        Calculate how well a grant matches the search criteria.

        Returns a score from 0.0 to 1.0.
        """
        score = 0.0
        factors = 0

        # Focus area match
        if criteria.focus_areas:
            focus_match = sum(
                1 for fa in criteria.focus_areas
                if any(fa.lower() in gfa.lower() for gfa in grant.focus_areas)
            )
            score += (focus_match / len(criteria.focus_areas)) * 0.4
            factors += 0.4

        # Geographic match
        if criteria.geographic_scope:
            if (criteria.geographic_scope.lower() in grant.geographic_scope.lower() or
                grant.geographic_scope.lower() == "national"):
                score += 0.2
            factors += 0.2

        # Amount match
        if criteria.min_amount or criteria.max_amount:
            try:
                amount_str = grant.amount
                amounts = re.findall(r'\$?([\d,]+)', amount_str)
                if amounts:
                    max_amount = float(amounts[-1].replace(',', ''))
                    if criteria.max_amount and max_amount <= criteria.max_amount:
                        score += 0.2
                    elif criteria.min_amount and max_amount >= criteria.min_amount:
                        score += 0.1
            except (ValueError, IndexError):
                pass
            factors += 0.2

        # Deadline match
        if criteria.deadline_after or criteria.deadline_before:
            deadline_ok = True
            if criteria.deadline_after and grant.deadline < criteria.deadline_after:
                deadline_ok = False
            if criteria.deadline_before and grant.deadline > criteria.deadline_before:
                deadline_ok = False
            if deadline_ok:
                score += 0.2
            factors += 0.2

        # Normalize score
        return min(1.0, score / factors if factors > 0 else 0.5)

    def _generate_match_reasoning(
        self,
        grant: GrantOpportunity,
        criteria: GrantSearchCriteria
    ) -> str:
        """
        Generate human-readable reasoning for why this grant matches.
        """
        reasons = []

        # Focus areas
        matching_areas = [
            fa for fa in criteria.focus_areas
            if any(fa.lower() in gfa.lower() for gfa in grant.focus_areas)
        ]
        if matching_areas:
            reasons.append(f"Matches focus areas: {', '.join(matching_areas)}")

        # Geographic
        if criteria.geographic_scope:
            if criteria.geographic_scope.lower() in grant.geographic_scope.lower():
                reasons.append(f"Available in {criteria.geographic_scope}")
            elif grant.geographic_scope.lower() == "national":
                reasons.append("National scope - available in all regions")

        # Deadline
        days_until = (grant.deadline - datetime.utcnow()).days
        if days_until > 0:
            reasons.append(f"Deadline in {days_until} days")

        return "; ".join(reasons) if reasons else "General match based on criteria"

    def analyze_grant(self, grant: GrantOpportunity) -> Dict[str, Any]:
        """
        Perform detailed analysis of a grant opportunity.

        Args:
            grant: The grant to analyze

        Returns:
            Analysis results including eligibility assessment,
            requirements breakdown, and recommendations
        """
        return {
            "grant_id": grant.id,
            "title": grant.title,
            "analysis_date": datetime.utcnow().isoformat(),
            "eligibility_assessment": {
                "requirements_count": len(grant.eligibility),
                "requirements": grant.eligibility,
                "estimated_match": "high" if grant.analysis_score > 0.7 else "medium" if grant.analysis_score > 0.4 else "low",
            },
            "requirements_breakdown": {
                "total_requirements": len(grant.requirements),
                "requirements": grant.requirements,
                "estimated_effort": "moderate",
            },
            "timeline": {
                "deadline": grant.deadline.isoformat(),
                "days_remaining": (grant.deadline - datetime.utcnow()).days,
                "recommended_start": "immediately" if (grant.deadline - datetime.utcnow()).days < 30 else "within 2 weeks",
            },
            "recommendations": [
                "Review eligibility requirements carefully",
                "Gather supporting documents early",
                "Contact funder with questions before deadline",
            ],
        }
