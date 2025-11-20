"""
Shoghi Commercial Agent System

Provides standardized framework for commercial agents operating within
Ohana communities with ethical constraints and full transparency.

Components:
- Fee Structure: Standardized, low-end fee schedules
- Agent Builder: Template for creating commercial agents
- Skills Package: Required ethical skills and constraints
- Registry: Community approval and lifecycle management
- Fee Processor: Payment collection and fund distribution
- Transparency: Monthly reporting for community oversight
"""

from .fee_structure import (
    ProductCategory,
    FeeModel,
    FeeConfig,
    FeeExample,
    SHOGHI_COMMERCIAL_FEES,
    FUND_DISTRIBUTION,
    get_fee_config,
    calculate_fee,
    distribute_fee,
    get_fee_examples
)

from .skills import (
    SkillCategory,
    Skill,
    REQUIRED_BASE_SKILLS,
    PRODUCT_SPECIFIC_SKILLS_TEMPLATE,
    COMMERCIAL_AGENT_CAPABILITIES,
    FORBIDDEN_TACTICS,
    DISCLOSURE_SCRIPT_TEMPLATE,
    CONSULTATIVE_QUESTIONS,
    generate_disclosure_script,
    get_skill_evaluation_checklist,
    validate_agent_skills
)

from .agent_builder import (
    CommercialAgentConfig,
    CommercialAgentBuilder
)

from .registry import (
    AgentStatus,
    ReviewCheckStatus,
    ReviewCheck,
    AgentSubmission,
    CommercialAgentRegistry
)

from .fee_processor import (
    TransactionStatus,
    ReferralTransaction,
    FundAllocation,
    CommercialFeeProcessor
)

from .transparency import (
    AgentActivityReport,
    RevenueReport,
    CommunityDecisionsReport,
    MonthlyTransparencyReport,
    CommercialTransparencyReport
)

__all__ = [
    # Fee Structure
    "ProductCategory",
    "FeeModel",
    "FeeConfig",
    "FeeExample",
    "SHOGHI_COMMERCIAL_FEES",
    "FUND_DISTRIBUTION",
    "get_fee_config",
    "calculate_fee",
    "distribute_fee",
    "get_fee_examples",

    # Skills
    "SkillCategory",
    "Skill",
    "REQUIRED_BASE_SKILLS",
    "PRODUCT_SPECIFIC_SKILLS_TEMPLATE",
    "COMMERCIAL_AGENT_CAPABILITIES",
    "FORBIDDEN_TACTICS",
    "DISCLOSURE_SCRIPT_TEMPLATE",
    "CONSULTATIVE_QUESTIONS",
    "generate_disclosure_script",
    "get_skill_evaluation_checklist",
    "validate_agent_skills",

    # Agent Builder
    "CommercialAgentConfig",
    "CommercialAgentBuilder",

    # Registry
    "AgentStatus",
    "ReviewCheckStatus",
    "ReviewCheck",
    "AgentSubmission",
    "CommercialAgentRegistry",

    # Fee Processor
    "TransactionStatus",
    "ReferralTransaction",
    "FundAllocation",
    "CommercialFeeProcessor",

    # Transparency
    "AgentActivityReport",
    "RevenueReport",
    "CommunityDecisionsReport",
    "MonthlyTransparencyReport",
    "CommercialTransparencyReport",
]

__version__ = "0.1.0"
