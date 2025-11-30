#!/usr/bin/env python3
"""
KALA VALUE SYSTEM
A value unit loosely pegged to the dollar for tracking in-kind contributions and services.

Kala is NOT a currency. It's a measurement unit that enables communities to:
- Record the in-kind value of contributions
- Track small acts of service
- Value non-monetary exchanges
- Recognize community participation

The dollar peg provides a consistent reference point for valuation while
maintaining the distinction that kala measures social value, not financial transactions.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

# Dollar peg: 1 kala ≈ $1 USD (loosely pegged)
KALA_TO_USD_RATE = 1.0


class ContributionType(Enum):
    """Types of contributions that can be valued in kala"""
    TIME = "time"                      # Volunteer time/service hours
    SKILL = "skill"                    # Professional skills shared
    RESOURCE = "resource"              # Material goods donated
    CARE = "care"                      # Elder care, child care, etc.
    FOOD = "food"                      # Food sharing and meals
    TRANSPORT = "transport"            # Transportation services
    COORDINATION = "coordination"      # Organizing and coordinating
    KNOWLEDGE = "knowledge"            # Teaching and mentoring
    CREATIVE = "creative"              # Art, music, cultural work
    OTHER = "other"                    # Other community contributions


@dataclass
class KalaContribution:
    """A single contribution valued in kala"""
    id: str
    contributor_id: str                # Who made the contribution
    recipient_id: Optional[str]        # Who received it (None = community)
    contribution_type: ContributionType
    description: str
    kala_value: float                  # Value in kala
    usd_equivalent: float              # Equivalent USD for reference
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    verified: bool = False             # Has this been verified/approved?
    tags: List[str] = field(default_factory=list)


@dataclass
class KalaAccount:
    """Tracks kala contributions for a community member or entity"""
    id: str
    name: str
    contributions_given: List[str] = field(default_factory=list)
    contributions_received: List[str] = field(default_factory=list)
    total_kala_given: float = 0.0
    total_kala_received: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class KalaValueSystem:
    """
    System for tracking and managing kala-valued contributions.

    This system helps communities:
    1. Record non-monetary contributions with consistent valuation
    2. Track volunteer time and services
    3. Recognize and value community participation
    4. Generate reports on community value creation
    """

    def __init__(self, use_crdt: bool = False, node_id: Optional[str] = None):
        """
        Initialize Kala Value System.

        Args:
            use_crdt: Use CRDT-backed accounts for distributed sync
            node_id: Node ID for CRDT backend (required if use_crdt=True)
        """
        self.contributions: Dict[str, KalaContribution] = {}
        self.accounts: Dict[str, KalaAccount] = {}
        self.crdt_accounts: Dict[str, Any] = {}  # CRDT-backed accounts
        self.exchange_rate = KALA_TO_USD_RATE
        self.use_crdt = use_crdt
        self.node_id = node_id

        # Initialize CRDT backend if requested
        if use_crdt:
            try:
                from vessels.crdt.kala import CRDTKalaAccount
                self.CRDTKalaAccount = CRDTKalaAccount
                logger.info(f"Kala Value System initialized with CRDT support (node: {node_id})")
            except ImportError as e:
                logger.error(f"Could not import CRDT support: {e}")
                raise

        logger.info(f"Kala Value System initialized (1 kala ≈ ${self.exchange_rate} USD)")

    def create_account(self, account_id: str, name: str) -> KalaAccount:
        """
        Create a new kala account for tracking contributions.

        If CRDT mode is enabled, creates a CRDT-backed account for
        distributed synchronization.
        """
        # Create regular account for tracking
        account = KalaAccount(
            id=account_id,
            name=name
        )
        self.accounts[account_id] = account

        # Create CRDT account if enabled
        if self.use_crdt:
            crdt_account = self.CRDTKalaAccount(
                account_id=account_id,
                node_id=self.node_id
            )
            self.crdt_accounts[account_id] = crdt_account
            logger.info(f"Created CRDT kala account: {name} ({account_id})")
        else:
            logger.info(f"Created kala account: {name} ({account_id})")

        return account

    def record_contribution(
        self,
        contributor_id: str,
        contribution_type: ContributionType,
        description: str,
        kala_value: float,
        recipient_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> KalaContribution:
        """
        Record a contribution valued in kala.

        Args:
            contributor_id: ID of person/entity making contribution
            contribution_type: Type of contribution from ContributionType enum
            description: Human-readable description
            kala_value: Value in kala (loosely pegged to USD)
            recipient_id: Optional specific recipient (None = whole community)
            metadata: Additional structured data about the contribution
            tags: Tags for categorization

        Returns:
            KalaContribution object
        """
        contribution_id = str(uuid.uuid4())

        contribution = KalaContribution(
            id=contribution_id,
            contributor_id=contributor_id,
            recipient_id=recipient_id,
            contribution_type=contribution_type,
            description=description,
            kala_value=kala_value,
            usd_equivalent=kala_value * self.exchange_rate,
            timestamp=datetime.now(),
            metadata=metadata or {},
            tags=tags or []
        )

        # Store contribution
        self.contributions[contribution_id] = contribution

        # Update accounts
        if contributor_id not in self.accounts:
            self.create_account(contributor_id, contributor_id)

        contributor = self.accounts[contributor_id]
        contributor.contributions_given.append(contribution_id)
        contributor.total_kala_given += kala_value

        # Update CRDT account if enabled (contributor gives kala)
        if self.use_crdt and contributor_id in self.crdt_accounts:
            self.crdt_accounts[contributor_id].debit(
                kala_value,
                f"Contribution: {description}"
            )

        # Update recipient account if specified
        if recipient_id:
            if recipient_id not in self.accounts:
                self.create_account(recipient_id, recipient_id)

            recipient = self.accounts[recipient_id]
            recipient.contributions_received.append(contribution_id)
            recipient.total_kala_received += kala_value

            # Update CRDT account if enabled (recipient receives kala)
            if self.use_crdt and recipient_id in self.crdt_accounts:
                self.crdt_accounts[recipient_id].credit(
                    kala_value,
                    f"Received: {description}"
                )

        logger.info(
            f"Recorded contribution: {contributor_id} -> "
            f"{recipient_id or 'community'}: {kala_value} kala "
            f"({contribution_type.value})"
        )

        return contribution

    def verify_contribution(self, contribution_id: str) -> bool:
        """Verify/approve a contribution"""
        if contribution_id in self.contributions:
            self.contributions[contribution_id].verified = True
            logger.info(f"Verified contribution: {contribution_id}")
            return True
        return False

    def get_contribution(self, contribution_id: str) -> Optional[KalaContribution]:
        """Get a specific contribution by ID"""
        return self.contributions.get(contribution_id)

    def get_account(self, account_id: str) -> Optional[KalaAccount]:
        """Get an account by ID"""
        return self.accounts.get(account_id)

    def get_account_balance(self, account_id: str) -> Dict[str, float]:
        """
        Get account balance summary.
        Note: This is NOT a financial balance, but a record of value given/received.
        """
        account = self.accounts.get(account_id)
        if not account:
            return {
                "given": 0.0,
                "received": 0.0,
                "net": 0.0,
                "usd_equivalent_given": 0.0,
                "usd_equivalent_received": 0.0
            }

        return {
            "given": account.total_kala_given,
            "received": account.total_kala_received,
            "net": account.total_kala_received - account.total_kala_given,
            "usd_equivalent_given": account.total_kala_given * self.exchange_rate,
            "usd_equivalent_received": account.total_kala_received * self.exchange_rate
        }

    def value_time_contribution(
        self,
        hours: float,
        skill_level: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate kala value for time contributions.

        Skill levels and their approximate hourly rates:
        - general: $15/hour (general volunteer work)
        - skilled: $35/hour (trades, nursing, teaching)
        - professional: $75/hour (specialized professional services)
        - expert: $150/hour (expert consultation)

        Args:
            hours: Number of hours contributed
            skill_level: Level of skill/expertise
            metadata: Additional context for valuation

        Returns:
            Kala value for the time contribution
        """
        hourly_rates = {
            "general": 15.0,
            "skilled": 35.0,
            "professional": 75.0,
            "expert": 150.0
        }

        rate = hourly_rates.get(skill_level, 15.0)
        kala_value = hours * rate

        logger.info(
            f"Valued time contribution: {hours} hours @ {skill_level} level "
            f"= {kala_value} kala"
        )

        return kala_value

    def value_resource_contribution(
        self,
        resource_description: str,
        market_value_usd: Optional[float] = None,
        estimated_kala: Optional[float] = None
    ) -> float:
        """
        Calculate kala value for resource contributions (food, materials, etc.)

        Args:
            resource_description: Description of resource
            market_value_usd: Market value in USD if known
            estimated_kala: Direct kala estimate if USD value unknown

        Returns:
            Kala value for the resource
        """
        if market_value_usd is not None:
            # Use market value as basis (1:1 with dollar peg)
            kala_value = market_value_usd
        elif estimated_kala is not None:
            # Use provided estimate
            kala_value = estimated_kala
        else:
            # Need either market value or estimate
            raise ValueError(
                "Must provide either market_value_usd or estimated_kala"
            )

        logger.info(
            f"Valued resource contribution: {resource_description} "
            f"= {kala_value} kala"
        )

        return kala_value

    def get_contributions_by_type(
        self,
        contribution_type: ContributionType,
        verified_only: bool = False
    ) -> List[KalaContribution]:
        """Get all contributions of a specific type"""
        contributions = [
            c for c in self.contributions.values()
            if c.contribution_type == contribution_type
        ]

        if verified_only:
            contributions = [c for c in contributions if c.verified]

        return sorted(contributions, key=lambda c: c.timestamp, reverse=True)

    def get_community_total(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        contribution_type: Optional[ContributionType] = None
    ) -> Dict[str, Any]:
        """
        Get total community kala value created in a time period.

        Args:
            start_date: Start of time period (None = all time)
            end_date: End of time period (None = now)
            contribution_type: Filter by type (None = all types)

        Returns:
            Summary of community value creation
        """
        contributions = list(self.contributions.values())

        # Apply filters
        if start_date:
            contributions = [c for c in contributions if c.timestamp >= start_date]
        if end_date:
            contributions = [c for c in contributions if c.timestamp <= end_date]
        if contribution_type:
            contributions = [c for c in contributions if c.contribution_type == contribution_type]

        total_kala = sum(c.kala_value for c in contributions)
        total_usd_equivalent = total_kala * self.exchange_rate

        # Count by type
        by_type = {}
        for c in contributions:
            type_name = c.contribution_type.value
            by_type[type_name] = by_type.get(type_name, 0) + c.kala_value

        return {
            "total_kala": total_kala,
            "total_usd_equivalent": total_usd_equivalent,
            "contribution_count": len(contributions),
            "by_type": by_type,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }

    def generate_report(
        self,
        account_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report on kala contributions.

        Args:
            account_id: Specific account (None = community-wide)
            start_date: Start of period
            end_date: End of period

        Returns:
            Detailed report dictionary
        """
        if account_id:
            # Individual account report
            account = self.accounts.get(account_id)
            if not account:
                return {"error": f"Account not found: {account_id}"}

            contributions = [
                self.contributions[cid]
                for cid in account.contributions_given
                if cid in self.contributions
            ]

            # Apply date filters
            if start_date:
                contributions = [c for c in contributions if c.timestamp >= start_date]
            if end_date:
                contributions = [c for c in contributions if c.timestamp <= end_date]

            return {
                "account": {
                    "id": account.id,
                    "name": account.name
                },
                "summary": self.get_account_balance(account_id),
                "contributions": [
                    {
                        "id": c.id,
                        "type": c.contribution_type.value,
                        "description": c.description,
                        "kala_value": c.kala_value,
                        "usd_equivalent": c.usd_equivalent,
                        "timestamp": c.timestamp.isoformat(),
                        "verified": c.verified
                    }
                    for c in contributions
                ]
            }
        else:
            # Community-wide report
            return {
                "community": self.get_community_total(start_date, end_date),
                "active_accounts": len(self.accounts),
                "total_contributions": len(self.contributions),
                "top_contributors": self._get_top_contributors(5)
            }

    def _get_top_contributors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top contributors by kala value given"""
        accounts = sorted(
            self.accounts.values(),
            key=lambda a: a.total_kala_given,
            reverse=True
        )

        return [
            {
                "id": a.id,
                "name": a.name,
                "total_kala_given": a.total_kala_given,
                "contribution_count": len(a.contributions_given)
            }
            for a in accounts[:limit]
        ]

    def merge_crdt_account(self, account_id: str, peer_crdt_account) -> None:
        """
        Merge CRDT account state with peer for synchronization.

        Args:
            account_id: Account to merge
            peer_crdt_account: CRDT account from peer node
        """
        if not self.use_crdt:
            logger.warning("CRDT not enabled, cannot merge accounts")
            return

        if account_id not in self.crdt_accounts:
            logger.warning(f"Account {account_id} not found in CRDT accounts")
            return

        # Merge CRDT states
        self.crdt_accounts[account_id] = self.crdt_accounts[account_id].merge_with(peer_crdt_account)
        logger.info(f"Merged CRDT account {account_id}, new balance: {self.crdt_accounts[account_id].balance()} kala")

    def get_crdt_balance(self, account_id: str) -> Optional[float]:
        """Get CRDT account balance."""
        if not self.use_crdt or account_id not in self.crdt_accounts:
            return None
        return self.crdt_accounts[account_id].balance()

    def export_crdt_accounts(self) -> Dict[str, Any]:
        """Export all CRDT accounts for persistence."""
        if not self.use_crdt:
            return {}
        return {
            account_id: crdt_account.to_dict()
            for account_id, crdt_account in self.crdt_accounts.items()
        }

    def import_crdt_accounts(self, crdt_data: Dict[str, Any]) -> None:
        """Import CRDT accounts from persistence."""
        if not self.use_crdt:
            return
        for account_id, account_data in crdt_data.items():
            crdt_account = self.CRDTKalaAccount.from_dict(account_data)
            self.crdt_accounts[account_id] = crdt_account
        logger.info(f"Imported {len(crdt_data)} CRDT accounts")

    def export_data(self) -> Dict[str, Any]:
        """Export all kala data for backup or analysis"""
        return {
            "exchange_rate": self.exchange_rate,
            "accounts": {
                aid: {
                    "id": a.id,
                    "name": a.name,
                    "total_kala_given": a.total_kala_given,
                    "total_kala_received": a.total_kala_received,
                    "created_at": a.created_at.isoformat()
                }
                for aid, a in self.accounts.items()
            },
            "contributions": {
                cid: {
                    "id": c.id,
                    "contributor_id": c.contributor_id,
                    "recipient_id": c.recipient_id,
                    "type": c.contribution_type.value,
                    "description": c.description,
                    "kala_value": c.kala_value,
                    "usd_equivalent": c.usd_equivalent,
                    "timestamp": c.timestamp.isoformat(),
                    "verified": c.verified,
                    "tags": c.tags,
                    "metadata": c.metadata
                }
                for cid, c in self.contributions.items()
            }
        }


# Example usage and common contribution valuation helpers
def value_elder_care_visit(hours: float) -> float:
    """Standard valuation for elder care visits"""
    system = KalaValueSystem()
    return system.value_time_contribution(hours, skill_level="skilled")


def value_meal_delivery(meals: int, cost_per_meal: float = 12.0) -> float:
    """Standard valuation for meal delivery"""
    return meals * cost_per_meal


def value_transportation(miles: float, rate_per_mile: float = 0.67) -> float:
    """Standard valuation for transportation (IRS mileage rate)"""
    return miles * rate_per_mile


# Global kala system instance
kala_system = KalaValueSystem()
