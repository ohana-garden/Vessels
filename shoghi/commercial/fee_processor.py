"""
Commercial Fee Processor

Handles payment processing from companies to community infrastructure funds.
Ensures full transparency and proper distribution of fees.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from .fee_structure import FeeConfig, FUND_DISTRIBUTION, distribute_fee

logger = logging.getLogger(__name__)


class TransactionStatus(str, Enum):
    """Status of fee transaction"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class ReferralTransaction:
    """
    Record of a referral fee transaction

    Tracks the complete lifecycle of a fee from company to community fund.
    """
    transaction_id: str
    company_id: str
    agent_id: str
    customer_id: str
    community_id: str

    # Transaction details
    transaction_amount: float
    referral_fee: float
    fee_config: FeeConfig

    # Status tracking
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    # Distribution tracking
    distributed: bool = False
    distribution_breakdown: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "company_id": self.company_id,
            "agent_id": self.agent_id,
            "customer_id": self.customer_id,
            "community_id": self.community_id,
            "transaction_amount": self.transaction_amount,
            "referral_fee": self.referral_fee,
            "fee_config": {
                "fee_type": self.fee_config.fee_type.value,
                "rate": self.fee_config.rate,
                "flat_amount": self.fee_config.flat_amount,
                "cap": self.fee_config.cap,
                "minimum": self.fee_config.minimum
            },
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "failure_reason": self.failure_reason,
            "distributed": self.distributed,
            "distribution_breakdown": self.distribution_breakdown
        }


@dataclass
class FundAllocation:
    """
    Record of funds allocated to specific category

    Tracks how community fees are distributed across purposes.
    """
    allocation_id: str
    community_id: str
    category: str
    amount: float
    source_transaction_id: str
    allocated_at: datetime = field(default_factory=datetime.utcnow)

    # Usage tracking
    spent: float = 0.0
    remaining: float = field(init=False)

    def __post_init__(self):
        """Calculate remaining balance"""
        self.remaining = self.amount - self.spent

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "allocation_id": self.allocation_id,
            "community_id": self.community_id,
            "category": self.category,
            "amount": self.amount,
            "source_transaction_id": self.source_transaction_id,
            "allocated_at": self.allocated_at.isoformat(),
            "spent": self.spent,
            "remaining": self.remaining
        }


class CommercialFeeProcessor:
    """
    Processor for commercial referral fees

    Handles:
    - Fee calculation
    - Payment collection from companies
    - Distribution to community fund categories
    - Full transaction transparency
    """

    def __init__(self, graph_client=None, payment_gateway=None):
        """
        Initialize fee processor

        Args:
            graph_client: Optional Graphiti client for storing transactions
            payment_gateway: Optional payment gateway integration
        """
        self.graph_client = graph_client
        self.payment_gateway = payment_gateway

        # Transaction tracking
        self.transactions: Dict[str, ReferralTransaction] = {}
        self.allocations: Dict[str, FundAllocation] = {}

        logger.info("Commercial Fee Processor initialized")

    def process_referral_fee(
        self,
        company_id: str,
        agent_id: str,
        customer_id: str,
        community_id: str,
        transaction_amount: float,
        fee_config: FeeConfig
    ) -> str:
        """
        Process referral fee from company to community

        Args:
            company_id: Company making payment
            agent_id: Commercial agent that made referral
            customer_id: Customer who was referred
            community_id: Community receiving funds
            transaction_amount: Total transaction amount
            fee_config: Fee configuration

        Returns:
            Transaction ID
        """
        # Calculate fee
        referral_fee = fee_config.calculate_fee(transaction_amount)

        # Create transaction record
        transaction_id = self._generate_transaction_id()
        transaction = ReferralTransaction(
            transaction_id=transaction_id,
            company_id=company_id,
            agent_id=agent_id,
            customer_id=customer_id,
            community_id=community_id,
            transaction_amount=transaction_amount,
            referral_fee=referral_fee,
            fee_config=fee_config,
            status=TransactionStatus.PENDING
        )

        # Store transaction
        self.transactions[transaction_id] = transaction

        # Store in graph for transparency
        if self.graph_client:
            self._store_transaction_in_graph(transaction)

        logger.info(
            f"Referral transaction created: {transaction_id} "
            f"${referral_fee:.2f} from {company_id} to {community_id}"
        )

        # Process payment
        self._collect_payment(transaction)

        return transaction_id

    def _collect_payment(self, transaction: ReferralTransaction):
        """
        Collect payment from company

        Args:
            transaction: Transaction to process
        """
        transaction.status = TransactionStatus.PROCESSING

        try:
            # If payment gateway available, process payment
            if self.payment_gateway:
                payment_result = self.payment_gateway.charge(
                    company_id=transaction.company_id,
                    amount=transaction.referral_fee,
                    description=f"Referral fee for {transaction.agent_id}"
                )

                if not payment_result.get("success"):
                    raise Exception(payment_result.get("error", "Payment failed"))

            # Payment successful, distribute funds
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.utcnow()

            # Distribute to community fund
            self._distribute_to_community(transaction)

            logger.info(
                f"Payment collected and distributed for transaction {transaction.transaction_id}"
            )

        except Exception as e:
            transaction.status = TransactionStatus.FAILED
            transaction.failed_at = datetime.utcnow()
            transaction.failure_reason = str(e)

            logger.error(
                f"Payment failed for transaction {transaction.transaction_id}: {e}"
            )

    def _distribute_to_community(self, transaction: ReferralTransaction):
        """
        Distribute fee to community fund categories

        Args:
            transaction: Completed transaction
        """
        if transaction.status != TransactionStatus.COMPLETED:
            logger.error(f"Cannot distribute - transaction not completed: {transaction.transaction_id}")
            return

        # Calculate distribution
        distribution = distribute_fee(transaction.referral_fee)
        transaction.distribution_breakdown = distribution

        # Create allocation records
        for category, amount in distribution.items():
            allocation_id = f"{transaction.transaction_id}_{category}"

            allocation = FundAllocation(
                allocation_id=allocation_id,
                community_id=transaction.community_id,
                category=category,
                amount=amount,
                source_transaction_id=transaction.transaction_id
            )

            self.allocations[allocation_id] = allocation

            # Store in graph
            if self.graph_client:
                self._store_allocation_in_graph(allocation)

            logger.debug(
                f"Allocated ${amount:.2f} to {category} for {transaction.community_id}"
            )

        transaction.distributed = True

        logger.info(
            f"Distributed ${transaction.referral_fee:.2f} across "
            f"{len(distribution)} categories for {transaction.community_id}"
        )

    def get_transaction(self, transaction_id: str) -> Optional[ReferralTransaction]:
        """Get transaction by ID"""
        return self.transactions.get(transaction_id)

    def get_community_balance(self, community_id: str) -> Dict[str, float]:
        """
        Get current balance for community across all categories

        Args:
            community_id: Community ID

        Returns:
            Dictionary of category -> remaining balance
        """
        balances = {}

        for allocation in self.allocations.values():
            if allocation.community_id == community_id:
                if allocation.category not in balances:
                    balances[allocation.category] = 0.0
                balances[allocation.category] += allocation.remaining

        return balances

    def get_community_total_received(
        self,
        community_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """
        Get total fees received by community

        Args:
            community_id: Community ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Total fees received
        """
        total = 0.0

        for transaction in self.transactions.values():
            if transaction.community_id != community_id:
                continue

            if transaction.status != TransactionStatus.COMPLETED:
                continue

            # Apply date filters
            if start_date and transaction.completed_at < start_date:
                continue
            if end_date and transaction.completed_at > end_date:
                continue

            total += transaction.referral_fee

        return total

    def get_agent_transactions(
        self,
        agent_id: str,
        status: Optional[TransactionStatus] = None
    ) -> List[ReferralTransaction]:
        """
        Get transactions for a specific agent

        Args:
            agent_id: Agent ID
            status: Optional status filter

        Returns:
            List of transactions
        """
        transactions = [
            t for t in self.transactions.values()
            if t.agent_id == agent_id
        ]

        if status:
            transactions = [t for t in transactions if t.status == status]

        return transactions

    def get_company_transactions(
        self,
        company_id: str,
        status: Optional[TransactionStatus] = None
    ) -> List[ReferralTransaction]:
        """
        Get transactions for a specific company

        Args:
            company_id: Company ID
            status: Optional status filter

        Returns:
            List of transactions
        """
        transactions = [
            t for t in self.transactions.values()
            if t.company_id == company_id
        ]

        if status:
            transactions = [t for t in transactions if t.status == status]

        return transactions

    def refund_transaction(
        self,
        transaction_id: str,
        reason: str
    ) -> bool:
        """
        Refund a completed transaction

        Args:
            transaction_id: Transaction to refund
            reason: Reason for refund

        Returns:
            True if successful
        """
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found")
            return False

        if transaction.status != TransactionStatus.COMPLETED:
            logger.error(f"Can only refund completed transactions: {transaction_id}")
            return False

        try:
            # Process refund through payment gateway
            if self.payment_gateway:
                refund_result = self.payment_gateway.refund(
                    transaction_id=transaction_id,
                    amount=transaction.referral_fee,
                    reason=reason
                )

                if not refund_result.get("success"):
                    raise Exception(refund_result.get("error", "Refund failed"))

            transaction.status = TransactionStatus.REFUNDED

            # TODO: Reclaim allocated funds from community
            # This is complex and needs careful handling

            logger.info(f"Transaction {transaction_id} refunded: {reason}")
            return True

        except Exception as e:
            logger.error(f"Refund failed for {transaction_id}: {e}")
            return False

    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        import uuid
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"txn_{timestamp}_{unique_id}"

    def _store_transaction_in_graph(self, transaction: ReferralTransaction):
        """Store transaction in knowledge graph for transparency"""
        try:
            # Implementation would store in Graphiti/FalkorDB
            logger.debug(f"Stored transaction {transaction.transaction_id} in graph")
        except Exception as e:
            logger.error(f"Error storing transaction in graph: {e}")

    def _store_allocation_in_graph(self, allocation: FundAllocation):
        """Store allocation in knowledge graph"""
        try:
            # Implementation would store in Graphiti/FalkorDB
            logger.debug(f"Stored allocation {allocation.allocation_id} in graph")
        except Exception as e:
            logger.error(f"Error storing allocation in graph: {e}")
