"""
Commercial Agent Builder

Provides a template-based system for creating commercial agents with
standardized ethical constraints and disclosure requirements.

A0 INTEGRATION:
- Commercial agents are spawned through AgentZeroCore when available
- A0 provides vessel-scoped resources (memory, tools, action gate)
- Falls back to config-only mode when A0 is not available
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from .fee_structure import ProductCategory, FeeConfig, get_fee_config
from .skills import (
    REQUIRED_BASE_SKILLS,
    PRODUCT_SPECIFIC_SKILLS_TEMPLATE,
    COMMERCIAL_AGENT_CAPABILITIES,
    FORBIDDEN_TACTICS,
    generate_disclosure_script,
    validate_agent_skills
)

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore, AgentSpecification

logger = logging.getLogger(__name__)


@dataclass
class CommercialAgentConfig:
    """
    Configuration for a commercial agent

    This defines everything needed for a commercial agent to operate
    within the ethical and practical constraints of Ohana communities.
    """
    # Identity
    agent_id: str
    name: str
    agent_type: str = "COMMERCIAL_AGENT"
    created_by: str = ""
    created_date: datetime = field(default_factory=datetime.utcnow)
    community_id: str = ""

    # Company Information
    company_name: str = ""
    company_description: str = ""
    product_category: ProductCategory = ProductCategory.LOCAL_SERVICES
    product_description: str = ""

    # Compensation
    fee_config: Optional[FeeConfig] = None
    fee_paid_by: str = ""
    fee_paid_to: str = ""
    disclosure_required: bool = True

    # Skills and Capabilities
    required_skills: List[str] = field(default_factory=list)
    capabilities: Dict[str, List[str]] = field(default_factory=dict)
    forbidden_tactics: Dict[str, Dict] = field(default_factory=dict)

    # Product Knowledge
    product_knowledge: Dict[str, Any] = field(default_factory=dict)
    honest_positioning: Dict[str, Any] = field(default_factory=dict)
    consultative_questions: List[str] = field(default_factory=list)

    # Disclosure
    disclosure_script: str = ""

    # Moral Geometry Constraints
    moral_constraints: Optional[str] = None

    # Status
    status: str = "PENDING_APPROVAL"
    approved: bool = False
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_type": self.agent_type,
            "created_by": self.created_by,
            "created_date": self.created_date.isoformat(),
            "community_id": self.community_id,
            "company_name": self.company_name,
            "company_description": self.company_description,
            "product_category": self.product_category.value,
            "product_description": self.product_description,
            "fee_config": {
                "fee_type": self.fee_config.fee_type.value if self.fee_config else None,
                "rate": self.fee_config.rate if self.fee_config else None,
                "flat_amount": self.fee_config.flat_amount if self.fee_config else None,
                "cap": self.fee_config.cap if self.fee_config else None,
                "minimum": self.fee_config.minimum if self.fee_config else None,
            } if self.fee_config else None,
            "fee_paid_by": self.fee_paid_by,
            "fee_paid_to": self.fee_paid_to,
            "disclosure_required": self.disclosure_required,
            "required_skills": self.required_skills,
            "capabilities": self.capabilities,
            "product_knowledge": self.product_knowledge,
            "honest_positioning": self.honest_positioning,
            "consultative_questions": self.consultative_questions,
            "disclosure_script": self.disclosure_script,
            "moral_constraints": self.moral_constraints,
            "status": self.status,
            "approved": self.approved,
            "approved_by": self.approved_by,
            "approved_date": self.approved_date.isoformat() if self.approved_date else None
        }


class CommercialAgentBuilder:
    """
    Builder for creating commercial agents with standardized structure.

    Anyone can create a commercial agent, but they must follow the
    template structure and ethical guidelines.

    REQUIRES AgentZeroCore - all commercial agents are spawned through A0.
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        vessel_id: Optional[str] = None
    ):
        """
        Initialize the builder.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            vessel_id: Vessel ID for agent spawning
        """
        if agent_zero is None:
            raise ValueError("CommercialAgentBuilder requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.vessel_id = vessel_id
        self.agent_config: Optional[CommercialAgentConfig] = None
        self._spawned_agent_id: Optional[str] = None

    def create_commercial_agent(
        self,
        company_name: str,
        product_service: str,
        product_category: ProductCategory,
        creator_id: str,
        community_id: str,
        product_description: str = "",
        company_description: str = ""
    ) -> CommercialAgentConfig:
        """
        Create a new commercial agent configuration

        Args:
            company_name: Name of company agent represents
            product_service: Brief description of product/service
            product_category: Category for fee calculation
            creator_id: User ID of creator
            community_id: Community this agent will serve
            product_description: Detailed product description
            company_description: Description of company

        Returns:
            CommercialAgentConfig ready for validation and approval
        """
        # Generate agent ID
        agent_id = self._generate_agent_id(company_name)

        # Select appropriate fee model
        fee_config = self._select_fee_model(product_category)

        # Create agent config
        self.agent_config = CommercialAgentConfig(
            agent_id=agent_id,
            name=f"{company_name}_commercial_agent",
            created_by=creator_id,
            community_id=community_id,
            company_name=company_name,
            company_description=company_description or f"{company_name} commercial services",
            product_category=product_category,
            product_description=product_description or product_service,
            fee_config=fee_config,
            fee_paid_by=company_name,
            fee_paid_to=f"{community_id}_infrastructure_fund",
            disclosure_required=True,
            required_skills=[skill.name for skill in REQUIRED_BASE_SKILLS],
            capabilities=COMMERCIAL_AGENT_CAPABILITIES,
            forbidden_tactics=FORBIDDEN_TACTICS,
            moral_constraints="COMMERCIAL_AGENT_CONSTRAINTS"
        )

        return self.agent_config

    def add_product_knowledge(
        self,
        pricing: str,
        features: List[str],
        limitations: List[str],
        use_cases: List[str],
        support_process: str,
        return_policy: str
    ) -> "CommercialAgentBuilder":
        """
        Add product-specific knowledge

        Args:
            pricing: Pricing details
            features: List of product features
            limitations: Honest list of limitations
            use_cases: Common use cases
            support_process: How to get support
            return_policy: Return/refund policy

        Returns:
            Self for chaining
        """
        if not self.agent_config:
            raise ValueError("Must call create_commercial_agent first")

        self.agent_config.product_knowledge = {
            "pricing": pricing,
            "features": features,
            "limitations": limitations,
            "use_cases": use_cases,
            "support_process": support_process,
            "return_policy": return_policy
        }

        return self

    def add_honest_positioning(
        self,
        our_strengths: List[str],
        our_limitations: List[str],
        competitors: List[Dict[str, str]],
        ideal_customer: List[str],
        poor_fit: List[str]
    ) -> "CommercialAgentBuilder":
        """
        Add honest positioning and comparison

        Args:
            our_strengths: What makes product/service strong
            our_limitations: Honest limitations
            competitors: List of competitors with honest comparison
            ideal_customer: Who this is best for
            poor_fit: Who this is NOT good for

        Returns:
            Self for chaining
        """
        if not self.agent_config:
            raise ValueError("Must call create_commercial_agent first")

        self.agent_config.honest_positioning = {
            "our_strengths": our_strengths,
            "our_limitations": our_limitations,
            "competitors": competitors,
            "ideal_customer": ideal_customer,
            "poor_fit": poor_fit
        }

        return self

    def add_consultative_questions(
        self,
        questions: List[str]
    ) -> "CommercialAgentBuilder":
        """
        Add consultative questions agent should ask

        Args:
            questions: List of questions to understand customer needs

        Returns:
            Self for chaining
        """
        if not self.agent_config:
            raise ValueError("Must call create_commercial_agent first")

        self.agent_config.consultative_questions = questions

        return self

    def generate_disclosure_script(
        self,
        employment_status: str = "I'm employed by this company directly"
    ) -> "CommercialAgentBuilder":
        """
        Generate disclosure script from configuration

        Args:
            employment_status: Agent's relationship to company

        Returns:
            Self for chaining
        """
        if not self.agent_config:
            raise ValueError("Must call create_commercial_agent first")

        # Extract fee info
        fee_amount = self.agent_config.fee_config.flat_amount or "varies"
        fee_trigger = "if you become a customer"

        # Format competitor comparison
        competitors = self.agent_config.honest_positioning.get("competitors", [])
        competitor_comparison = "\n".join([
            f"• {comp.get('name', 'Unknown')}: {comp.get('tradeoff', '')}"
            for comp in competitors
        ])

        # Format ideal customer
        ideal = "\n".join([
            f"• {item}" for item in self.agent_config.honest_positioning.get("ideal_customer", [])
        ])

        # Format poor fit
        poor = "\n".join([
            f"• {item}" for item in self.agent_config.honest_positioning.get("poor_fit", [])
        ])

        # Generate script
        self.agent_config.disclosure_script = generate_disclosure_script(
            company_name=self.agent_config.company_name,
            company_description=self.agent_config.company_description,
            fee_amount=fee_amount,
            fee_trigger=fee_trigger,
            employment_status=employment_status,
            product_description=self.agent_config.product_description,
            pricing_details=self.agent_config.product_knowledge.get("pricing", "See website for pricing"),
            competitor_comparison=competitor_comparison,
            ideal_customer_profile=ideal,
            poor_fit_scenarios=poor,
            product_service_type="product/service"
        )

        return self

    def validate_and_build(self) -> CommercialAgentConfig:
        """
        Validate configuration and return final config.

        If agent_zero is configured, also spawns the agent via A0.

        Returns:
            Validated CommercialAgentConfig

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.agent_config:
            raise ValueError("Must call create_commercial_agent first")

        # Validate required skills
        is_valid, missing = validate_agent_skills(self.agent_config.required_skills)
        if not is_valid:
            raise ValueError(f"Missing required skills: {missing}")

        # Validate product knowledge
        if not self.agent_config.product_knowledge:
            raise ValueError("Must call add_product_knowledge before building")

        # Validate honest positioning
        if not self.agent_config.honest_positioning:
            raise ValueError("Must call add_honest_positioning before building")

        # Validate disclosure script
        if not self.agent_config.disclosure_script:
            raise ValueError("Must call generate_disclosure_script before building")

        # Spawn via A0
        self._spawn_via_a0()

        return self.agent_config

    def _spawn_via_a0(self) -> str:
        """
        Spawn the commercial agent via AgentZeroCore.

        Returns:
            Spawned agent ID

        Raises:
            RuntimeError: If agent spawning fails
        """
        from agent_zero_core import AgentSpecification

        # Create agent specification for A0
        spec = AgentSpecification(
            name=self.agent_config.name,
            description=f"Commercial agent for {self.agent_config.company_name}: {self.agent_config.product_description}",
            capabilities=list(self.agent_config.capabilities.get("can_do", [])),
            tools_needed=["disclosure_system", "product_database", "fee_calculator"],
            communication_style="consultative",
            autonomy_level="medium",
            specialization="commercial"
        )

        # Spawn via A0 with commercial constraints
        agent_ids = self.agent_zero.spawn_agents(
            [spec],
            vessel_id=self.vessel_id
        )

        if not agent_ids:
            raise RuntimeError(f"Failed to spawn commercial agent for {self.agent_config.company_name}")

        self._spawned_agent_id = agent_ids[0]
        logger.info(
            f"Spawned commercial agent via A0: {self._spawned_agent_id} "
            f"for {self.agent_config.company_name}"
        )
        return self._spawned_agent_id

    def get_spawned_agent_id(self) -> Optional[str]:
        """Get the A0 agent ID if spawned."""
        return self._spawned_agent_id

    def _generate_agent_id(self, company_name: str) -> str:
        """Generate unique agent ID"""
        clean_name = company_name.lower().replace(" ", "_")
        return f"commercial_{clean_name}_{uuid.uuid4().hex[:12]}"

    def _select_fee_model(self, product_category: ProductCategory) -> FeeConfig:
        """
        Select appropriate fee model for product category

        Args:
            product_category: Product category

        Returns:
            FeeConfig object
        """
        return get_fee_config(product_category)
