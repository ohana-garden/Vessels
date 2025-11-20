"""
Commercial Agent Fee Structure

Standardized fee schedule for commercial agents serving Ohana communities.
All fees are kept at the low end of industry standards and flow to community
infrastructure funds.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class ProductCategory(str, Enum):
    """Categories for commercial products and services"""
    DIGITAL_PRODUCTS_SAAS = "digital_products_saas"
    PHYSICAL_PRODUCTS = "physical_products"
    LOCAL_SERVICES = "local_services"
    PROFESSIONAL_SERVICES = "professional_services"
    GIG_ECONOMY = "gig_economy"
    SUBSCRIPTIONS = "subscriptions"


class FeeModel(str, Enum):
    """Types of fee models"""
    PERCENTAGE_CAPPED = "percentage_capped"
    FLAT_FEE = "flat_fee"
    ONE_TIME = "one_time"


@dataclass
class FeeConfig:
    """
    Configuration for a specific fee model

    Attributes:
        fee_type: Type of fee model (percentage, flat, one-time)
        rate: Percentage rate (if applicable)
        flat_amount: Flat fee amount (if applicable)
        cap: Maximum fee amount
        minimum: Minimum fee amount
        requires_qualification: Whether fee requires customer qualification
        one_time_only: Whether fee is only paid once per customer
    """
    fee_type: FeeModel
    rate: Optional[float] = None
    flat_amount: Optional[float] = None
    cap: Optional[float] = None
    minimum: Optional[float] = None
    requires_qualification: bool = False
    one_time_only: bool = False

    def calculate_fee(self, transaction_amount: float) -> float:
        """
        Calculate fee based on transaction amount

        Args:
            transaction_amount: The transaction amount

        Returns:
            Calculated fee amount
        """
        if self.fee_type == FeeModel.FLAT_FEE or self.fee_type == FeeModel.ONE_TIME:
            return self.flat_amount or 0.0

        elif self.fee_type == FeeModel.PERCENTAGE_CAPPED:
            fee = transaction_amount * (self.rate or 0.0)

            # Apply cap if specified
            if self.cap:
                fee = min(fee, self.cap)

            # Apply minimum if specified
            if self.minimum:
                fee = max(fee, self.minimum)

            return fee

        return 0.0


@dataclass
class FeeExample:
    """Example of fee calculation for a specific product price"""
    product_price: float
    calculated_fee: float
    description: str


# Standardized Fee Schedule (Conservative/Low-End)
SHOGHI_COMMERCIAL_FEES: Dict[ProductCategory, Dict] = {
    ProductCategory.DIGITAL_PRODUCTS_SAAS: {
        "commission": "20% of first month OR $25 flat (whichever lower)",
        "fee_config": FeeConfig(
            fee_type=FeeModel.PERCENTAGE_CAPPED,
            rate=0.20,
            cap=25.00,
            minimum=2.00
        ),
        "examples": [
            FeeExample(10.0, 2.00, "$10/mo app: $2 commission"),
            FeeExample(50.0, 10.00, "$50/mo service: $10 commission"),
            FeeExample(200.0, 25.00, "$200/mo software: $25 commission (capped)")
        ],
        "paid_by": "Product company",
        "paid_to": "Community infrastructure fund"
    },

    ProductCategory.PHYSICAL_PRODUCTS: {
        "commission": "3-5% of sale",
        "fee_config": FeeConfig(
            fee_type=FeeModel.PERCENTAGE_CAPPED,
            rate=0.03,  # Conservative 3%
            cap=100.00,
            minimum=1.50
        ),
        "examples": [
            FeeExample(50.0, 1.50, "$50 product: $1.50"),
            FeeExample(500.0, 15.00, "$500 appliance: $15"),
            FeeExample(5000.0, 100.00, "$5000 solar: $100 (capped)")
        ],
        "paid_by": "Product company",
        "paid_to": "Community infrastructure fund"
    },

    ProductCategory.LOCAL_SERVICES: {
        "commission": "$10-25 per qualified referral",
        "fee_config": FeeConfig(
            fee_type=FeeModel.FLAT_FEE,
            flat_amount=15.00,
            requires_qualification=True
        ),
        "examples": [
            FeeExample(0, 10.00, "handyman: $10"),
            FeeExample(0, 15.00, "meal_delivery: $15"),
            FeeExample(0, 20.00, "transport_service: $20"),
            FeeExample(0, 25.00, "major_home_service: $25")
        ],
        "qualified_means": "Customer actually books/uses service",
        "paid_by": "Service provider",
        "paid_to": "Community infrastructure fund"
    },

    ProductCategory.PROFESSIONAL_SERVICES: {
        "commission": "$25-50 per client",
        "fee_config": FeeConfig(
            fee_type=FeeModel.FLAT_FEE,
            flat_amount=35.00,
            requires_qualification=True
        ),
        "examples": [
            FeeExample(0, 25.00, "tax_prep: $25"),
            FeeExample(0, 35.00, "legal_consult: $35"),
            FeeExample(0, 25.00, "contractor_quote: $25")
        ],
        "paid_by": "Professional service provider",
        "paid_to": "Community infrastructure fund"
    },

    ProductCategory.GIG_ECONOMY: {
        "commission": "$5-15 per signup",
        "fee_config": FeeConfig(
            fee_type=FeeModel.FLAT_FEE,
            flat_amount=10.00,
            requires_qualification=True
        ),
        "examples": [
            FeeExample(0, 5.00, "food_delivery_driver: $5"),
            FeeExample(0, 10.00, "rideshare_driver: $10"),
            FeeExample(0, 10.00, "task_service: $10")
        ],
        "requires": "Worker completes qualifying activity",
        "paid_by": "Platform company",
        "paid_to": "Community infrastructure fund"
    },

    ProductCategory.SUBSCRIPTIONS: {
        "commission": "$5-10 per signup",
        "fee_config": FeeConfig(
            fee_type=FeeModel.ONE_TIME,
            flat_amount=8.00,
            one_time_only=True
        ),
        "examples": [
            FeeExample(0, 8.00, "meal_kit: $8"),
            FeeExample(0, 5.00, "streaming: $5"),
            FeeExample(0, 10.00, "subscription_box: $10")
        ],
        "paid_by": "Subscription company",
        "paid_to": "Community infrastructure fund"
    }
}


# Community Fund Distribution (60/20/15/5 split)
FUND_DISTRIBUTION = {
    "infrastructure": 0.60,        # Servers, tools, maintenance
    "servant_development": 0.20,   # Improving AI servants
    "community_discretionary": 0.15,  # Community decides usage
    "transparency_audit": 0.05     # Audit commercial interactions
}


def get_fee_config(category: ProductCategory) -> FeeConfig:
    """
    Get fee configuration for a product category

    Args:
        category: Product category

    Returns:
        FeeConfig object
    """
    return SHOGHI_COMMERCIAL_FEES[category]["fee_config"]


def calculate_fee(category: ProductCategory, transaction_amount: float) -> float:
    """
    Calculate fee for a transaction

    Args:
        category: Product category
        transaction_amount: Transaction amount

    Returns:
        Calculated fee
    """
    config = get_fee_config(category)
    return config.calculate_fee(transaction_amount)


def distribute_fee(total_fee: float) -> Dict[str, float]:
    """
    Distribute fee according to community fund allocation

    Args:
        total_fee: Total fee collected

    Returns:
        Dictionary of allocations
    """
    return {
        category: total_fee * percentage
        for category, percentage in FUND_DISTRIBUTION.items()
    }


def get_fee_examples(category: ProductCategory) -> List[FeeExample]:
    """
    Get example fee calculations for a category

    Args:
        category: Product category

    Returns:
        List of fee examples
    """
    return SHOGHI_COMMERCIAL_FEES[category]["examples"]
