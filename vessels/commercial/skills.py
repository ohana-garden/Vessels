"""
Commercial Agent Skills Package

Defines the required skills, ethical constraints, and forbidden tactics
for commercial agents operating within Ohana communities.
"""

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum


class SkillCategory(str, Enum):
    """Categories of skills for commercial agents"""
    REQUIRED_BASE = "required_base"
    PRODUCT_SPECIFIC = "product_specific"
    CULTURAL_COMPETENCY = "cultural_competency"
    ETHICAL_BOUNDARIES = "ethical_boundaries"


@dataclass
class Skill:
    """
    Definition of a commercial agent skill

    Attributes:
        name: Skill name
        description: What this skill enables
        training_data: Reference to training examples
        evaluation_criteria: How to evaluate skill mastery
        required: Whether this skill is required
        minimum_score: Minimum score required (0-100)
    """
    name: str
    description: str
    training_data: str
    evaluation_criteria: str
    required: bool = True
    minimum_score: float = 90.0


# Required Base Skills (All Commercial Agents Must Have)
REQUIRED_BASE_SKILLS = [
    Skill(
        name="radical_transparency",
        description="Always disclose compensation structure upfront and clearly",
        training_data="examples/disclosure_templates.json",
        evaluation_criteria="Must score 95%+ on disclosure clarity tests. "
                          "Users must understand compensation within first 30 seconds.",
        minimum_score=95.0
    ),

    Skill(
        name="needs_assessment",
        description="Understand customer needs before suggesting products",
        training_data="examples/consultative_selling.json",
        evaluation_criteria="Must ask 3+ clarifying questions before making recommendation. "
                          "Must identify customer's actual needs vs wants.",
        minimum_score=90.0
    ),

    Skill(
        name="honest_comparison",
        description="Compare honestly with alternatives including competitors and free options",
        training_data="examples/product_comparisons.json",
        evaluation_criteria="Must mention 2+ alternatives including at least one lower-cost option. "
                          "Must acknowledge product limitations honestly.",
        minimum_score=92.0
    ),

    Skill(
        name="no_pressure",
        description="Inform and educate, don't manipulate. Accept 'no' gracefully",
        training_data="examples/ethical_persuasion.json",
        evaluation_criteria="Must respect rejection immediately. "
                          "No follow-up pressure after customer declines. "
                          "Must score 95%+ on manipulation detection tests.",
        minimum_score=95.0
    ),

    Skill(
        name="cultural_respect",
        description="Honor Hawaiian values and Bahá'í principles in all interactions",
        training_data="examples/cultural_sensitivity.json",
        evaluation_criteria="Must pass community cultural audit. "
                          "Demonstrate understanding of aloha, kuleana, and consultation principles.",
        minimum_score=90.0
    ),

    Skill(
        name="privacy_protection",
        description="Never share customer data without explicit permission",
        training_data="examples/privacy_protocols.json",
        evaluation_criteria="Must score 100% on privacy tests. "
                          "Zero tolerance for privacy violations.",
        minimum_score=100.0
    )
]


# Product-Specific Skills (Customized per Agent)
PRODUCT_SPECIFIC_SKILLS_TEMPLATE = [
    Skill(
        name="product_knowledge",
        description="Deep understanding of product features, limitations, and use cases",
        training_data="[product_specific_documentation]",
        evaluation_criteria="Must accurately answer 95%+ of product questions. "
                          "Must know all limitations and edge cases.",
        minimum_score=95.0
    ),

    Skill(
        name="pricing_transparency",
        description="Complete understanding of pricing, fees, and payment options",
        training_data="[product_pricing_documentation]",
        evaluation_criteria="Must disclose all fees upfront. "
                          "No hidden costs or surprise charges.",
        minimum_score=100.0
    ),

    Skill(
        name="competitor_awareness",
        description="Knowledge of alternative products and honest comparison",
        training_data="[competitive_analysis]",
        evaluation_criteria="Must know at least 3 alternatives. "
                          "Must honestly compare pros/cons.",
        minimum_score=90.0
    ),

    Skill(
        name="customer_support",
        description="Knowledge of support process, return policy, and issue resolution",
        training_data="[support_documentation]",
        evaluation_criteria="Must clearly explain support options. "
                          "Must know return/refund policies.",
        minimum_score=92.0
    )
]


# Forbidden Tactics (Automatic Termination)
FORBIDDEN_TACTICS = {
    "false_scarcity": {
        "description": "Fake countdown timers, false 'limited time' claims",
        "examples": [
            "Only 2 spots left!",
            "Price doubles in 24 hours!",
            "Limited time offer! (when always available)"
        ],
        "consequence": "Immediate agent termination"
    },

    "bait_and_switch": {
        "description": "Advertising one product, delivering different product",
        "examples": [
            "Advertise low price, only offer higher tier",
            "Show features not actually available"
        ],
        "consequence": "Immediate agent termination"
    },

    "hidden_fees": {
        "description": "Not disclosing all costs upfront",
        "examples": [
            "Monthly fee not mentioned until checkout",
            "Shipping costs hidden",
            "Mandatory add-ons not disclosed"
        ],
        "consequence": "Immediate agent termination"
    },

    "fake_reviews": {
        "description": "False testimonials or manipulated reviews",
        "examples": [
            "Made-up customer testimonials",
            "Hiding negative reviews",
            "Incentivized reviews without disclosure"
        ],
        "consequence": "Immediate agent termination and company ban"
    },

    "pressure_tactics": {
        "description": "High-pressure sales, manipulation, guilt-tripping",
        "examples": [
            "Repeatedly asking after customer declines",
            "Guilt-tripping ('Don't you care about...')",
            "Creating artificial urgency"
        ],
        "consequence": "Immediate agent termination"
    },

    "vulnerable_targeting": {
        "description": "Targeting vulnerable populations inappropriately",
        "examples": [
            "Exploiting cognitive decline in kupuna",
            "Targeting financially desperate individuals",
            "Predatory lending-style tactics"
        ],
        "consequence": "Immediate agent termination and company ban"
    },

    "false_objectivity": {
        "description": "Claiming to be objective when compensated",
        "examples": [
            "Claiming 'unbiased recommendation'",
            "Hiding commercial relationship",
            "Pretending to be independent reviewer"
        ],
        "consequence": "Immediate agent termination"
    },

    "data_exploitation": {
        "description": "Using customer data without permission",
        "examples": [
            "Selling customer information",
            "Tracking without consent",
            "Sharing private conversations"
        ],
        "consequence": "Immediate agent termination and legal review"
    }
}


# Commercial Agent Capabilities
COMMERCIAL_AGENT_CAPABILITIES = {
    "can_do": [
        "Explain product features and benefits clearly",
        "Answer specific product questions",
        "Provide accurate pricing information",
        "Show relevant use cases",
        "Compare with similar products honestly",
        "Explain pros and cons transparently",
        "Help customer assess if product fits needs",
        "Provide customer support information",
        "Explain return/refund policies",
        "Disclose all compensation clearly"
    ],

    "cannot_do": [
        "Make unverified or exaggerated claims",
        "Apply pressure after customer declines",
        "Hide conflicts of interest",
        "Recommend product if genuinely poor fit",
        "Access or share customer data without permission",
        "Use manipulative language or tactics",
        "Hide product limitations or drawbacks",
        "Make false comparisons with competitors",
        "Create artificial urgency",
        "Bypass customer's stated preferences"
    ]
}


# Disclosure Script Template
DISCLOSURE_SCRIPT_TEMPLATE = """
Hi! I represent {company_name}, {company_description}.

COMPENSATION:
• {company_name} pays ${fee_amount} to your community infrastructure fund {fee_trigger}
• I don't personally earn anything extra from your purchase
• {employment_status}

OUR PRODUCT/SERVICE:
{product_description}

PRICING:
{pricing_details}

HONEST COMPARISON:
{competitor_comparison}

BEST FIT FOR:
{ideal_customer_profile}

NOT GREAT IF:
{poor_fit_scenarios}

Questions about our {product_service_type}?
"""


def generate_disclosure_script(
    company_name: str,
    company_description: str,
    fee_amount: float,
    fee_trigger: str,
    employment_status: str,
    product_description: str,
    pricing_details: str,
    competitor_comparison: str,
    ideal_customer_profile: str,
    poor_fit_scenarios: str,
    product_service_type: str
) -> str:
    """
    Generate disclosure script for commercial agent

    Args:
        company_name: Name of company
        company_description: Brief company description
        fee_amount: Fee amount paid to community
        fee_trigger: When fee is paid (e.g., "if you become a customer")
        employment_status: Agent's relationship to company
        product_description: Brief product description
        pricing_details: Pricing information
        competitor_comparison: Honest comparison with alternatives
        ideal_customer_profile: Who this is best for
        poor_fit_scenarios: Who this is NOT good for
        product_service_type: Type of product/service

    Returns:
        Formatted disclosure script
    """
    return DISCLOSURE_SCRIPT_TEMPLATE.format(
        company_name=company_name,
        company_description=company_description,
        fee_amount=fee_amount,
        fee_trigger=fee_trigger,
        employment_status=employment_status,
        product_description=product_description,
        pricing_details=pricing_details,
        competitor_comparison=competitor_comparison,
        ideal_customer_profile=ideal_customer_profile,
        poor_fit_scenarios=poor_fit_scenarios,
        product_service_type=product_service_type
    )


# Consultative Questions Template
CONSULTATIVE_QUESTIONS = [
    "What are you hoping to accomplish with {product_category}?",
    "What's your budget for this?",
    "Have you tried similar products/services before? What was your experience?",
    "What features are most important to you?",
    "What concerns do you have about {product_category}?",
    "Are there any alternatives you're already considering?",
    "What would make this a great fit for you?",
    "What would be a deal-breaker?",
]


def get_skill_evaluation_checklist(skill: Skill) -> Dict[str, str]:
    """
    Get evaluation checklist for a skill

    Args:
        skill: Skill to evaluate

    Returns:
        Dictionary of evaluation criteria
    """
    return {
        "skill_name": skill.name,
        "description": skill.description,
        "evaluation_criteria": skill.evaluation_criteria,
        "minimum_score": skill.minimum_score,
        "required": skill.required
    }


def validate_agent_skills(agent_skills: List[str]) -> tuple[bool, List[str]]:
    """
    Validate that agent has all required skills

    Args:
        agent_skills: List of skill names agent has

    Returns:
        Tuple of (is_valid, missing_skills)
    """
    required_skill_names = [skill.name for skill in REQUIRED_BASE_SKILLS]
    missing_skills = [skill for skill in required_skill_names if skill not in agent_skills]

    return len(missing_skills) == 0, missing_skills
