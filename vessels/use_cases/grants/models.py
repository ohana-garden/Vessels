"""
Grant Data Models

Defines the core data structures for grant management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class GrantStatus(Enum):
    """Status of a grant opportunity or application."""
    DISCOVERED = "discovered"
    ANALYZING = "analyzing"
    READY_TO_APPLY = "ready_to_apply"
    APPLICATION_DRAFT = "application_draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    AWARDED = "awarded"
    REJECTED = "rejected"
    CLOSED = "closed"


@dataclass
class GrantOpportunity:
    """
    Represents a grant funding opportunity.

    Attributes:
        id: Unique identifier for the grant
        title: Grant title
        description: Full description of the grant
        funder: Organization providing the funding
        amount: Funding amount (as string to handle ranges)
        deadline: Application deadline
        eligibility: List of eligibility requirements
        focus_areas: Areas the grant focuses on
        geographic_scope: Geographic requirements/limitations
        application_url: URL to apply
        contact_info: Contact information for inquiries
        requirements: Application requirements
        status: Current status of the grant
        discovery_date: When the grant was discovered
        analysis_score: Score indicating match quality (0.0 - 1.0)
        match_reasoning: Explanation of why this grant matches
        vessel_id: The vessel this grant is associated with
    """
    id: str
    title: str
    description: str
    funder: str
    amount: str
    deadline: datetime
    eligibility: List[str]
    focus_areas: List[str]
    geographic_scope: str
    application_url: str
    contact_info: Dict[str, str]
    requirements: List[str]
    status: GrantStatus
    discovery_date: datetime
    analysis_score: float = 0.0
    match_reasoning: str = ""
    vessel_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "funder": self.funder,
            "amount": self.amount,
            "deadline": self.deadline.isoformat(),
            "eligibility": self.eligibility,
            "focus_areas": self.focus_areas,
            "geographic_scope": self.geographic_scope,
            "application_url": self.application_url,
            "contact_info": self.contact_info,
            "requirements": self.requirements,
            "status": self.status.value,
            "discovery_date": self.discovery_date.isoformat(),
            "analysis_score": self.analysis_score,
            "match_reasoning": self.match_reasoning,
            "vessel_id": self.vessel_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GrantOpportunity":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            funder=data.get("funder", ""),
            amount=data.get("amount", ""),
            deadline=datetime.fromisoformat(data["deadline"]) if isinstance(data["deadline"], str) else data["deadline"],
            eligibility=data.get("eligibility", []),
            focus_areas=data.get("focus_areas", []),
            geographic_scope=data.get("geographic_scope", ""),
            application_url=data.get("application_url", ""),
            contact_info=data.get("contact_info", {}),
            requirements=data.get("requirements", []),
            status=GrantStatus(data.get("status", "discovered")),
            discovery_date=datetime.fromisoformat(data["discovery_date"]) if isinstance(data.get("discovery_date"), str) else datetime.utcnow(),
            analysis_score=data.get("analysis_score", 0.0),
            match_reasoning=data.get("match_reasoning", ""),
            vessel_id=data.get("vessel_id"),
        )


@dataclass
class GrantApplication:
    """
    Represents a grant application being prepared or submitted.

    Attributes:
        id: Unique identifier for the application
        grant_id: ID of the grant being applied for
        vessel_id: The vessel this application belongs to
        applicant_info: Information about the applicant organization
        narrative_sections: Application narrative sections
        budget: Budget breakdown
        supporting_documents: List of document paths/references
        compliance_checklist: Checklist of requirements met
        submission_date: When the application was submitted
        status: Current status
        version: Version number for drafts
        created_at: When the application was created
        updated_at: When the application was last updated
    """
    id: str
    grant_id: str
    vessel_id: str
    applicant_info: Dict[str, Any]
    narrative_sections: Dict[str, str] = field(default_factory=dict)
    budget: Dict[str, Any] = field(default_factory=dict)
    supporting_documents: List[str] = field(default_factory=list)
    compliance_checklist: Dict[str, bool] = field(default_factory=dict)
    submission_date: Optional[datetime] = None
    status: GrantStatus = GrantStatus.APPLICATION_DRAFT
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "grant_id": self.grant_id,
            "vessel_id": self.vessel_id,
            "applicant_info": self.applicant_info,
            "narrative_sections": self.narrative_sections,
            "budget": self.budget,
            "supporting_documents": self.supporting_documents,
            "compliance_checklist": self.compliance_checklist,
            "submission_date": self.submission_date.isoformat() if self.submission_date else None,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GrantApplication":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            grant_id=data["grant_id"],
            vessel_id=data["vessel_id"],
            applicant_info=data.get("applicant_info", {}),
            narrative_sections=data.get("narrative_sections", {}),
            budget=data.get("budget", {}),
            supporting_documents=data.get("supporting_documents", []),
            compliance_checklist=data.get("compliance_checklist", {}),
            submission_date=datetime.fromisoformat(data["submission_date"]) if data.get("submission_date") else None,
            status=GrantStatus(data.get("status", "application_draft")),
            version=data.get("version", 1),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
        )


@dataclass
class GrantSearchCriteria:
    """Criteria for searching grants."""
    focus_areas: List[str] = field(default_factory=list)
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    geographic_scope: Optional[str] = None
    deadline_after: Optional[datetime] = None
    deadline_before: Optional[datetime] = None
    funders: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
