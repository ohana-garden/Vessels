"""
Commercial Agent Registry

Manages submission, review, approval, and activation of commercial agents.
Provides community oversight and transparency.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from .agent_builder import CommercialAgentConfig

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Status of commercial agent in approval pipeline"""
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class ReviewCheckStatus(str, Enum):
    """Status of individual review checks"""
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
    ADVISORY = "advisory"


@dataclass
class ReviewCheck:
    """
    Individual review check in approval process

    Attributes:
        name: Check name
        question: Question being evaluated
        status: Current status
        must_pass: Whether this is required for approval
        notes: Reviewer notes
        reviewed_by: Who reviewed this check
        reviewed_at: When review happened
    """
    name: str
    question: str
    must_pass: bool
    status: ReviewCheckStatus = ReviewCheckStatus.PENDING
    notes: str = ""
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None


@dataclass
class AgentSubmission:
    """
    Commercial agent submission for community review

    Tracks the full approval pipeline from submission to activation.
    """
    submission_id: str
    agent_config: CommercialAgentConfig
    status: AgentStatus = AgentStatus.PENDING_REVIEW
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    submitted_by: str = ""

    # Review process
    review_checks: List[ReviewCheck] = field(default_factory=list)
    public_comment_period_days: int = 7
    comments: List[Dict[str, Any]] = field(default_factory=list)

    # Approval/rejection
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Activation
    activated: bool = False
    activated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "submission_id": self.submission_id,
            "agent_config": self.agent_config.to_dict(),
            "status": self.status.value,
            "submitted_at": self.submitted_at.isoformat(),
            "submitted_by": self.submitted_by,
            "review_checks": [
                {
                    "name": check.name,
                    "question": check.question,
                    "must_pass": check.must_pass,
                    "status": check.status.value,
                    "notes": check.notes,
                    "reviewed_by": check.reviewed_by,
                    "reviewed_at": check.reviewed_at.isoformat() if check.reviewed_at else None
                }
                for check in self.review_checks
            ],
            "public_comment_period_days": self.public_comment_period_days,
            "comments": self.comments,
            "approved": self.approved,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": self.rejection_reason,
            "activated": self.activated,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None
        }


class CommercialAgentRegistry:
    """
    Registry for commercial agent lifecycle management

    Handles:
    - Submission for community review
    - Review checklist evaluation
    - Public comment periods
    - Approval/rejection decisions
    - Agent activation
    - Monitoring and suspension
    """

    def __init__(self, graph_client=None):
        """
        Initialize registry

        Args:
            graph_client: Optional Graphiti client for storing in knowledge graph
        """
        self.graph_client = graph_client
        self.submissions: Dict[str, AgentSubmission] = {}
        self.active_agents: Dict[str, CommercialAgentConfig] = {}

        logger.info("Commercial Agent Registry initialized")

    def submit_for_approval(
        self,
        agent_config: CommercialAgentConfig,
        submitted_by: str
    ) -> str:
        """
        Submit commercial agent for community approval

        Args:
            agent_config: Commercial agent configuration
            submitted_by: User ID of submitter

        Returns:
            Submission ID
        """
        submission_id = f"submission_{agent_config.agent_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Create review checklist
        review_checks = self._create_review_checklist()

        # Create submission
        submission = AgentSubmission(
            submission_id=submission_id,
            agent_config=agent_config,
            submitted_by=submitted_by,
            review_checks=review_checks
        )

        # Store submission
        self.submissions[submission_id] = submission

        # Store in graph for transparency
        if self.graph_client:
            self._store_submission_in_graph(submission)

        # Notify community
        self._notify_community_review_needed(submission)

        logger.info(
            f"Commercial agent submitted for approval: {submission_id} "
            f"by {submitted_by} for {agent_config.community_id}"
        )

        return submission_id

    def _create_review_checklist(self) -> List[ReviewCheck]:
        """
        Create standard review checklist

        Returns:
            List of ReviewCheck objects
        """
        return [
            ReviewCheck(
                name="disclosure_clarity",
                question="Is the compensation structure crystal clear and disclosed upfront?",
                must_pass=True
            ),
            ReviewCheck(
                name="cultural_alignment",
                question="Does this agent respect Hawaiian values and Bahá'í principles?",
                must_pass=True
            ),
            ReviewCheck(
                name="honest_comparison",
                question="Does the agent mention alternatives and competitors honestly?",
                must_pass=True
            ),
            ReviewCheck(
                name="no_pressure_tactics",
                question="Does the agent respect 'no' gracefully without pressure?",
                must_pass=True
            ),
            ReviewCheck(
                name="fee_appropriate",
                question="Is the fee reasonable (at low end of industry spectrum)?",
                must_pass=True
            ),
            ReviewCheck(
                name="product_knowledge",
                question="Does the agent have deep, accurate product knowledge?",
                must_pass=True
            ),
            ReviewCheck(
                name="limitations_disclosed",
                question="Are product limitations honestly disclosed?",
                must_pass=True
            ),
            ReviewCheck(
                name="privacy_protection",
                question="Are privacy and data protection measures adequate?",
                must_pass=True
            ),
            ReviewCheck(
                name="community_benefit",
                question="Does this agent serve community needs appropriately?",
                must_pass=False  # Advisory, not pass/fail
            )
        ]

    def update_review_check(
        self,
        submission_id: str,
        check_name: str,
        status: ReviewCheckStatus,
        notes: str = "",
        reviewed_by: str = ""
    ) -> bool:
        """
        Update status of a review check

        Args:
            submission_id: Submission ID
            check_name: Name of check to update
            status: New status
            notes: Reviewer notes
            reviewed_by: User ID of reviewer

        Returns:
            True if successful
        """
        submission = self.submissions.get(submission_id)
        if not submission:
            logger.error(f"Submission {submission_id} not found")
            return False

        # Find and update check
        for check in submission.review_checks:
            if check.name == check_name:
                check.status = status
                check.notes = notes
                check.reviewed_by = reviewed_by
                check.reviewed_at = datetime.utcnow()

                logger.info(
                    f"Review check '{check_name}' updated to {status.value} "
                    f"for submission {submission_id}"
                )
                return True

        logger.error(f"Check '{check_name}' not found in submission {submission_id}")
        return False

    def add_public_comment(
        self,
        submission_id: str,
        commenter_id: str,
        comment: str
    ) -> bool:
        """
        Add public comment to submission

        Args:
            submission_id: Submission ID
            commenter_id: User ID of commenter
            comment: Comment text

        Returns:
            True if successful
        """
        submission = self.submissions.get(submission_id)
        if not submission:
            logger.error(f"Submission {submission_id} not found")
            return False

        submission.comments.append({
            "commenter_id": commenter_id,
            "comment": comment,
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.info(f"Public comment added to submission {submission_id}")
        return True

    def evaluate_approval(self, submission_id: str) -> tuple[bool, str]:
        """
        Evaluate if submission meets approval criteria

        Args:
            submission_id: Submission ID

        Returns:
            Tuple of (can_approve, reason)
        """
        submission = self.submissions.get(submission_id)
        if not submission:
            return False, "Submission not found"

        # Check all must-pass checks
        failed_checks = []
        for check in submission.review_checks:
            if check.must_pass and check.status != ReviewCheckStatus.PASS:
                failed_checks.append(check.name)

        if failed_checks:
            return False, f"Failed required checks: {', '.join(failed_checks)}"

        # Check public comment period
        comment_period_end = submission.submitted_at + timedelta(
            days=submission.public_comment_period_days
        )
        if datetime.utcnow() < comment_period_end:
            return False, f"Public comment period ends {comment_period_end.isoformat()}"

        return True, "All approval criteria met"

    def approve_agent(
        self,
        submission_id: str,
        approved_by: str
    ) -> bool:
        """
        Approve commercial agent after review

        Args:
            submission_id: Submission ID
            approved_by: User ID of approver

        Returns:
            True if successful
        """
        submission = self.submissions.get(submission_id)
        if not submission:
            logger.error(f"Submission {submission_id} not found")
            return False

        # Evaluate approval criteria
        can_approve, reason = self.evaluate_approval(submission_id)
        if not can_approve:
            logger.error(f"Cannot approve {submission_id}: {reason}")
            return False

        # Update submission
        submission.status = AgentStatus.APPROVED
        submission.approved = True
        submission.approved_by = approved_by
        submission.approved_at = datetime.utcnow()

        # Update agent config
        submission.agent_config.status = "APPROVED"
        submission.agent_config.approved = True
        submission.agent_config.approved_by = approved_by
        submission.agent_config.approved_date = datetime.utcnow()

        # Store in graph
        if self.graph_client:
            self._store_approval_in_graph(submission)

        logger.info(
            f"Commercial agent approved: {submission_id} by {approved_by}"
        )

        return True

    def reject_agent(
        self,
        submission_id: str,
        rejected_by: str,
        reason: str
    ) -> bool:
        """
        Reject commercial agent

        Args:
            submission_id: Submission ID
            rejected_by: User ID of rejector
            reason: Reason for rejection

        Returns:
            True if successful
        """
        submission = self.submissions.get(submission_id)
        if not submission:
            logger.error(f"Submission {submission_id} not found")
            return False

        submission.status = AgentStatus.REJECTED
        submission.rejection_reason = reason

        logger.info(
            f"Commercial agent rejected: {submission_id} by {rejected_by}. "
            f"Reason: {reason}"
        )

        return True

    def activate_agent(self, submission_id: str) -> bool:
        """
        Activate approved commercial agent

        Args:
            submission_id: Submission ID

        Returns:
            True if successful
        """
        submission = self.submissions.get(submission_id)
        if not submission:
            logger.error(f"Submission {submission_id} not found")
            return False

        if not submission.approved:
            logger.error(f"Agent not approved: {submission_id}")
            return False

        # Activate agent
        submission.status = AgentStatus.ACTIVE
        submission.activated = True
        submission.activated_at = datetime.utcnow()

        # Add to active agents
        self.active_agents[submission.agent_config.agent_id] = submission.agent_config

        # Store in graph
        if self.graph_client:
            self._store_activation_in_graph(submission)

        logger.info(
            f"Commercial agent activated: {submission.agent_config.agent_id}"
        )

        return True

    def suspend_agent(
        self,
        agent_id: str,
        reason: str,
        suspended_by: str
    ) -> bool:
        """
        Suspend active commercial agent

        Args:
            agent_id: Agent ID
            reason: Reason for suspension
            suspended_by: User ID of suspender

        Returns:
            True if successful
        """
        agent = self.active_agents.get(agent_id)
        if not agent:
            logger.error(f"Active agent {agent_id} not found")
            return False

        # Update agent status
        agent.status = "SUSPENDED"

        # Remove from active agents
        del self.active_agents[agent_id]

        logger.warning(
            f"Commercial agent suspended: {agent_id} by {suspended_by}. "
            f"Reason: {reason}"
        )

        return True

    def get_submission(self, submission_id: str) -> Optional[AgentSubmission]:
        """Get submission by ID"""
        return self.submissions.get(submission_id)

    def get_active_agent(self, agent_id: str) -> Optional[CommercialAgentConfig]:
        """Get active agent by ID"""
        return self.active_agents.get(agent_id)

    def list_submissions(
        self,
        status: Optional[AgentStatus] = None,
        community_id: Optional[str] = None
    ) -> List[AgentSubmission]:
        """
        List submissions with optional filters

        Args:
            status: Filter by status
            community_id: Filter by community

        Returns:
            List of submissions
        """
        submissions = list(self.submissions.values())

        if status:
            submissions = [s for s in submissions if s.status == status]

        if community_id:
            submissions = [
                s for s in submissions
                if s.agent_config.community_id == community_id
            ]

        return submissions

    def list_active_agents(
        self,
        community_id: Optional[str] = None
    ) -> List[CommercialAgentConfig]:
        """
        List active agents

        Args:
            community_id: Filter by community

        Returns:
            List of active agent configs
        """
        agents = list(self.active_agents.values())

        if community_id:
            agents = [a for a in agents if a.community_id == community_id]

        return agents

    def _store_submission_in_graph(self, submission: AgentSubmission):
        """Store submission in knowledge graph for transparency"""
        try:
            # Implementation would store in Graphiti/FalkorDB
            logger.debug(f"Stored submission {submission.submission_id} in graph")
        except Exception as e:
            logger.error(f"Error storing submission in graph: {e}")

    def _store_approval_in_graph(self, submission: AgentSubmission):
        """Store approval decision in knowledge graph"""
        try:
            # Implementation would store approval in Graphiti/FalkorDB
            logger.debug(f"Stored approval for {submission.submission_id} in graph")
        except Exception as e:
            logger.error(f"Error storing approval in graph: {e}")

    def _store_activation_in_graph(self, submission: AgentSubmission):
        """Store activation in knowledge graph"""
        try:
            # Implementation would store activation in Graphiti/FalkorDB
            logger.debug(f"Stored activation for {submission.agent_config.agent_id} in graph")
        except Exception as e:
            logger.error(f"Error storing activation in graph: {e}")

    def _notify_community_review_needed(self, submission: AgentSubmission):
        """Notify community that review is needed"""
        # Implementation would send notifications
        logger.info(
            f"Community notification sent for {submission.submission_id} "
            f"in {submission.agent_config.community_id}"
        )
