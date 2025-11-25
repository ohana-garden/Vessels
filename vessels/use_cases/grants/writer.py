"""
Grant Application Writer

Generates grant application content for discovered opportunities.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import GrantApplication, GrantOpportunity, GrantStatus

logger = logging.getLogger(__name__)


class GrantApplicationWriter:
    """
    Service for writing grant applications.

    Generates application narratives, budgets, and supporting materials
    based on the grant requirements and vessel context.
    """

    def __init__(self, vessel_id: str, applicant_info: Dict[str, Any]):
        """
        Initialize writer for a vessel.

        Args:
            vessel_id: The vessel ID
            applicant_info: Information about the applicant organization
        """
        self.vessel_id = vessel_id
        self.applicant_info = applicant_info

    def create_application(
        self,
        grant: GrantOpportunity,
        custom_sections: Optional[Dict[str, str]] = None
    ) -> GrantApplication:
        """
        Create a new grant application.

        Args:
            grant: The grant opportunity to apply for
            custom_sections: Optional custom narrative sections

        Returns:
            New GrantApplication with generated content
        """
        application = GrantApplication(
            id=f"app-{uuid.uuid4().hex[:12]}",
            grant_id=grant.id,
            vessel_id=self.vessel_id,
            applicant_info=self.applicant_info,
            status=GrantStatus.APPLICATION_DRAFT,
        )

        # Generate narrative sections
        application.narrative_sections = self._generate_narratives(grant)

        # Override with custom sections if provided
        if custom_sections:
            application.narrative_sections.update(custom_sections)

        # Generate budget
        application.budget = self._generate_budget(grant)

        # Create compliance checklist
        application.compliance_checklist = self._create_checklist(grant)

        logger.info(f"Created application {application.id} for grant {grant.id}")
        return application

    def _generate_narratives(self, grant: GrantOpportunity) -> Dict[str, str]:
        """
        Generate narrative sections for the application.

        Args:
            grant: The grant being applied for

        Returns:
            Dictionary of section name to content
        """
        org_name = self.applicant_info.get("organization_name", "Our Organization")
        mission = self.applicant_info.get("mission", "serving our community")
        community = self.applicant_info.get("community", "the community")

        return {
            "executive_summary": self._generate_executive_summary(grant, org_name, mission),
            "statement_of_need": self._generate_need_statement(grant, community),
            "project_description": self._generate_project_description(grant, org_name),
            "methodology": self._generate_methodology(grant),
            "evaluation_plan": self._generate_evaluation_plan(grant),
            "sustainability_plan": self._generate_sustainability_plan(grant, org_name),
            "organizational_capacity": self._generate_organizational_capacity(org_name, mission),
        }

    def _generate_executive_summary(
        self,
        grant: GrantOpportunity,
        org_name: str,
        mission: str
    ) -> str:
        """Generate executive summary section."""
        focus_areas = ", ".join(grant.focus_areas[:3]) if grant.focus_areas else "community development"

        return f"""EXECUTIVE SUMMARY

{org_name} respectfully requests {grant.amount} from {grant.funder} to support our {focus_areas} initiative.

Our organization is dedicated to {mission}, and this project aligns directly with the funder's priorities in {focus_areas}.

Through this program, we will:
- Deliver direct services to community members in need
- Build sustainable capacity for long-term impact
- Measure and report outcomes aligned with funder priorities

The requested funding will enable us to expand our reach and deepen our impact in {grant.geographic_scope}.
"""

    def _generate_need_statement(self, grant: GrantOpportunity, community: str) -> str:
        """Generate statement of need section."""
        focus = grant.focus_areas[0] if grant.focus_areas else "community services"

        return f"""STATEMENT OF NEED

{community} faces significant challenges in {focus}. This need is urgent and growing.

Key statistics demonstrate the depth of this challenge:
- Demand for services continues to exceed available resources
- Underserved populations lack access to critical support
- Without intervention, outcomes will continue to decline

Our community members deserve better. This grant will help us address these needs directly.

The target population for this project includes those most affected by these challenges, with priority given to underserved and vulnerable community members.
"""

    def _generate_project_description(self, grant: GrantOpportunity, org_name: str) -> str:
        """Generate project description section."""
        return f"""PROJECT DESCRIPTION

{org_name} proposes a comprehensive program to address the identified needs through evidence-based approaches.

PROJECT GOALS:
1. Increase access to services for underserved community members
2. Improve outcomes through targeted interventions
3. Build sustainable capacity for long-term community benefit

ACTIVITIES:
- Direct service delivery to target population
- Community outreach and education
- Capacity building and training
- Partnership development with local organizations

TIMELINE:
- Months 1-3: Program setup and staff training
- Months 4-9: Full program implementation
- Months 10-12: Evaluation and sustainability planning

TARGET POPULATION:
We will serve community members most in need, with specific focus on those who face barriers to accessing existing services.
"""

    def _generate_methodology(self, grant: GrantOpportunity) -> str:
        """Generate methodology section."""
        return """METHODOLOGY

Our approach is grounded in evidence-based practices and informed by community input.

THEORETICAL FRAMEWORK:
Our program design draws on established research demonstrating the effectiveness of community-based approaches.

IMPLEMENTATION APPROACH:
- Culturally responsive service delivery
- Trauma-informed practices
- Strengths-based engagement
- Collaborative partnerships

STAFF AND QUALIFICATIONS:
Our team brings extensive experience in program delivery, including:
- Experienced program managers
- Trained direct service staff
- Community liaisons with local connections

PARTNERSHIPS:
We collaborate with local organizations to maximize impact and avoid duplication of services.
"""

    def _generate_evaluation_plan(self, grant: GrantOpportunity) -> str:
        """Generate evaluation plan section."""
        return """EVALUATION PLAN

We are committed to measuring and demonstrating the impact of this program.

OUTCOME MEASURES:
1. Number of individuals served
2. Satisfaction rates among participants
3. Measurable improvements in target outcomes
4. Community-level indicators of change

DATA COLLECTION METHODS:
- Participant intake and tracking
- Pre/post assessments
- Satisfaction surveys
- Community feedback sessions

EVALUATION TIMELINE:
- Baseline data collection at program start
- Quarterly progress monitoring
- Mid-term evaluation at 6 months
- Final evaluation and reporting at project end

LEARNING AND IMPROVEMENT:
Evaluation findings will inform ongoing program improvements and future funding requests.
"""

    def _generate_sustainability_plan(self, grant: GrantOpportunity, org_name: str) -> str:
        """Generate sustainability plan section."""
        return f"""SUSTAINABILITY PLAN

{org_name} is committed to sustaining the impact of this program beyond the grant period.

FINANCIAL SUSTAINABILITY:
- Diversified funding through multiple grant sources
- Development of earned revenue opportunities
- Individual donor cultivation
- In-kind support from community partners

PROGRAMMATIC SUSTAINABILITY:
- Building community capacity through training
- Documentation of best practices
- Knowledge transfer to partner organizations
- Integration into organizational core services

ORGANIZATIONAL CAPACITY:
Our organization has demonstrated ability to sustain programs through:
- Strong financial management
- Effective board governance
- Community trust and support
"""

    def _generate_organizational_capacity(self, org_name: str, mission: str) -> str:
        """Generate organizational capacity section."""
        return f"""ORGANIZATIONAL CAPACITY

{org_name} has the capacity and experience to successfully implement this program.

MISSION AND HISTORY:
Our organization is dedicated to {mission}. We have served our community with integrity and effectiveness.

GOVERNANCE:
- Active and engaged Board of Directors
- Clear policies and procedures
- Regular financial audits
- Transparent operations

EXPERIENCE:
We have successfully managed similar programs and grants, demonstrating:
- Effective program implementation
- Accurate financial management
- Timely and comprehensive reporting
- Strong community relationships

INFRASTRUCTURE:
Our organization maintains the administrative infrastructure necessary to support this program, including appropriate facilities, technology, and systems.
"""

    def _generate_budget(self, grant: GrantOpportunity) -> Dict[str, Any]:
        """
        Generate a budget for the application.

        Args:
            grant: The grant being applied for

        Returns:
            Budget breakdown
        """
        # Parse amount to estimate budget
        try:
            import re
            amounts = re.findall(r'\$?([\d,]+)', grant.amount)
            if amounts:
                total = float(amounts[0].replace(',', ''))
            else:
                total = 50000  # Default
        except (ValueError, IndexError):
            total = 50000

        # Standard budget breakdown
        return {
            "total_request": total,
            "categories": {
                "personnel": {
                    "amount": total * 0.55,
                    "description": "Program staff salaries and benefits",
                    "items": [
                        {"name": "Program Coordinator", "amount": total * 0.35},
                        {"name": "Direct Service Staff", "amount": total * 0.15},
                        {"name": "Benefits (20%)", "amount": total * 0.05},
                    ]
                },
                "operations": {
                    "amount": total * 0.20,
                    "description": "Program operating expenses",
                    "items": [
                        {"name": "Supplies and materials", "amount": total * 0.08},
                        {"name": "Communications", "amount": total * 0.04},
                        {"name": "Travel/transportation", "amount": total * 0.05},
                        {"name": "Evaluation costs", "amount": total * 0.03},
                    ]
                },
                "indirect": {
                    "amount": total * 0.15,
                    "description": "Indirect costs (administrative overhead)",
                    "items": [
                        {"name": "Administrative support", "amount": total * 0.10},
                        {"name": "Facilities", "amount": total * 0.05},
                    ]
                },
                "contingency": {
                    "amount": total * 0.10,
                    "description": "Contingency and miscellaneous",
                    "items": []
                },
            },
            "matching_funds": {
                "required": False,
                "amount": 0,
                "sources": [],
            },
            "budget_narrative": self._generate_budget_narrative(total),
        }

    def _generate_budget_narrative(self, total: float) -> str:
        """Generate budget narrative justification."""
        return f"""BUDGET NARRATIVE

The requested budget of ${total:,.0f} has been carefully developed to ensure efficient use of funds while achieving program objectives.

PERSONNEL ({total * 0.55:,.0f}):
Personnel costs represent the largest budget category, reflecting the direct service nature of this program. Staff will deliver services, coordinate activities, and ensure quality implementation.

OPERATIONS ({total * 0.20:,.0f}):
Operating expenses support direct program delivery, including supplies, communications, and travel to serve community members.

INDIRECT COSTS ({total * 0.15:,.0f}):
Indirect costs cover administrative support necessary to maintain program quality and compliance.

CONTINGENCY ({total * 0.10:,.0f}):
A modest contingency allows for unforeseen needs and ensures program continuity.

This budget represents a cost-effective approach to achieving significant community impact.
"""

    def _create_checklist(self, grant: GrantOpportunity) -> Dict[str, bool]:
        """
        Create compliance checklist based on grant requirements.

        Args:
            grant: The grant being applied for

        Returns:
            Checklist dictionary
        """
        checklist = {
            "executive_summary_complete": False,
            "need_statement_complete": False,
            "project_description_complete": False,
            "methodology_complete": False,
            "evaluation_plan_complete": False,
            "sustainability_plan_complete": False,
            "organizational_capacity_complete": False,
            "budget_complete": False,
            "budget_narrative_complete": False,
        }

        # Add grant-specific requirements
        for req in grant.requirements:
            key = req.lower().replace(" ", "_").replace("(", "").replace(")", "")[:50]
            checklist[f"req_{key}"] = False

        return checklist

    def update_section(
        self,
        application: GrantApplication,
        section_name: str,
        content: str
    ) -> GrantApplication:
        """
        Update a specific section of an application.

        Args:
            application: The application to update
            section_name: Name of the section
            content: New content

        Returns:
            Updated application
        """
        application.narrative_sections[section_name] = content
        application.updated_at = datetime.utcnow()

        # Update checklist if section is standard
        checklist_key = f"{section_name}_complete"
        if checklist_key in application.compliance_checklist:
            application.compliance_checklist[checklist_key] = True

        return application

    def finalize_application(self, application: GrantApplication) -> GrantApplication:
        """
        Finalize application for submission.

        Args:
            application: The application to finalize

        Returns:
            Finalized application
        """
        # Check all required sections
        incomplete = [
            k for k, v in application.compliance_checklist.items()
            if not v and not k.startswith("req_")
        ]

        if incomplete:
            logger.warning(f"Application {application.id} has incomplete sections: {incomplete}")

        application.status = GrantStatus.READY_TO_APPLY
        application.updated_at = datetime.utcnow()
        application.version += 1

        return application
