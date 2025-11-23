"""
G-Counter (Grow-only Counter) CRDT for Kala contribution tracking.

Provides conflict-free replication of monotonically increasing
Kala balances across distributed Vessels nodes.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from collections import defaultdict
import uuid


class GCounter:
    """
    Grow-only Counter CRDT.

    State-based CRDT for distributed counters that only increment.
    Each node maintains its own counter, and the global value is
    the sum of all node counters.

    Properties:
    - Commutative: merge(A, B) = merge(B, A)
    - Associative: merge(merge(A, B), C) = merge(A, merge(B, C))
    - Idempotent: merge(A, A) = A
    - Monotonic: value never decreases

    Perfect for tracking contributions where values only grow
    (Kala credits, contribution counts, etc.)
    """

    def __init__(self, node_id: Optional[str] = None):
        """
        Initialize G-Counter.

        Args:
            node_id: Unique identifier for this node
        """
        self.node_id = node_id or str(uuid.uuid4())
        # Map: node_id -> increment value
        self.increments: Dict[str, float] = defaultdict(float)

    def increment(self, value: float = 1.0) -> None:
        """
        Increment local counter.

        Args:
            value: Amount to increment (must be non-negative)

        Raises:
            ValueError: If value is negative
        """
        if value < 0:
            raise ValueError("G-Counter can only increment (value must be non-negative)")

        self.increments[self.node_id] += value

    def value(self) -> float:
        """
        Get current counter value (sum of all increments).

        Returns:
            Total counter value
        """
        return sum(self.increments.values())

    def merge(self, other: 'GCounter') -> 'GCounter':
        """
        Merge with another G-Counter.

        Merge rule: For each node, take the maximum increment value.

        Args:
            other: Other G-Counter to merge

        Returns:
            New merged G-Counter
        """
        merged = GCounter(self.node_id)

        # Take max increment for each node
        all_nodes = set(self.increments.keys()) | set(other.increments.keys())
        for node in all_nodes:
            merged.increments[node] = max(
                self.increments.get(node, 0.0),
                other.increments.get(node, 0.0)
            )

        return merged

    def to_dict(self) -> Dict[str, any]:
        """Serialize to dictionary."""
        return {
            "node_id": self.node_id,
            "increments": dict(self.increments)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'GCounter':
        """Deserialize from dictionary."""
        counter = cls(data["node_id"])
        counter.increments = defaultdict(float, data["increments"])
        return counter

    def __repr__(self) -> str:
        return f"GCounter(node={self.node_id}, value={self.value()})"


class PNCounter:
    """
    PN-Counter (Positive-Negative Counter) CRDT.

    Extends G-Counter to support both increments and decrements.
    Uses two G-Counters: one for increments (P), one for decrements (N).
    Value = P - N

    Useful for balances that can increase or decrease.
    """

    def __init__(self, node_id: Optional[str] = None):
        """
        Initialize PN-Counter.

        Args:
            node_id: Unique identifier for this node
        """
        self.node_id = node_id or str(uuid.uuid4())
        self.positive = GCounter(node_id)
        self.negative = GCounter(node_id)

    def increment(self, value: float = 1.0) -> None:
        """Increment counter."""
        self.positive.increment(value)

    def decrement(self, value: float = 1.0) -> None:
        """Decrement counter."""
        self.negative.increment(value)

    def value(self) -> float:
        """Get current counter value (P - N)."""
        return self.positive.value() - self.negative.value()

    def merge(self, other: 'PNCounter') -> 'PNCounter':
        """Merge with another PN-Counter."""
        merged = PNCounter(self.node_id)
        merged.positive = self.positive.merge(other.positive)
        merged.negative = self.negative.merge(other.negative)
        return merged

    def to_dict(self) -> Dict[str, any]:
        """Serialize to dictionary."""
        return {
            "node_id": self.node_id,
            "positive": self.positive.to_dict(),
            "negative": self.negative.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'PNCounter':
        """Deserialize from dictionary."""
        counter = cls(data["node_id"])
        counter.positive = GCounter.from_dict(data["positive"])
        counter.negative = GCounter.from_dict(data["negative"])
        return counter

    def __repr__(self) -> str:
        return f"PNCounter(node={self.node_id}, value={self.value()})"


@dataclass
class KalaTransaction:
    """
    Record of a Kala transaction.

    Stored alongside CRDT counter for audit trail.
    """
    transaction_id: str
    timestamp: str  # ISO format
    amount: float
    transaction_type: str  # "credit" or "debit"
    reason: str
    node_id: str


class CRDTKalaAccount:
    """
    CRDT-backed Kala account for distributed contribution tracking.

    Uses PN-Counter for balance and maintains transaction log
    for audit trail.
    """

    def __init__(self, account_id: str, node_id: Optional[str] = None):
        """
        Initialize Kala account.

        Args:
            account_id: Account identifier (e.g., user ID, community ID)
            node_id: Vessels node identifier
        """
        self.account_id = account_id
        self.counter = PNCounter(node_id)
        self.transactions: list[KalaTransaction] = []

    def credit(self, amount: float, reason: str) -> None:
        """
        Credit Kala to account.

        Args:
            amount: Kala amount (must be positive)
            reason: Description of credit

        Raises:
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        self.counter.increment(amount)

        # Log transaction
        from datetime import datetime
        transaction = KalaTransaction(
            transaction_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            amount=amount,
            transaction_type="credit",
            reason=reason,
            node_id=self.counter.node_id
        )
        self.transactions.append(transaction)

    def debit(self, amount: float, reason: str) -> None:
        """
        Debit Kala from account.

        Args:
            amount: Kala amount (must be positive)
            reason: Description of debit

        Raises:
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Debit amount must be positive")

        self.counter.decrement(amount)

        # Log transaction
        from datetime import datetime
        transaction = KalaTransaction(
            transaction_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            amount=amount,
            transaction_type="debit",
            reason=reason,
            node_id=self.counter.node_id
        )
        self.transactions.append(transaction)

    def balance(self) -> float:
        """Get current Kala balance."""
        return self.counter.value()

    def merge_with(self, other: 'CRDTKalaAccount') -> 'CRDTKalaAccount':
        """
        Merge with another Kala account.

        Args:
            other: Other Kala account (must have same account_id)

        Returns:
            New merged Kala account

        Raises:
            ValueError: If account IDs don't match
        """
        if self.account_id != other.account_id:
            raise ValueError(
                f"Cannot merge accounts with different IDs: "
                f"{self.account_id} vs {other.account_id}"
            )

        merged = CRDTKalaAccount(self.account_id, self.counter.node_id)
        merged.counter = self.counter.merge(other.counter)

        # Merge transaction logs (union, deduplicated by transaction_id)
        transaction_dict = {
            t.transaction_id: t for t in self.transactions + other.transactions
        }
        merged.transactions = list(transaction_dict.values())

        # Sort by timestamp
        merged.transactions.sort(key=lambda t: t.timestamp)

        return merged

    def transaction_history(self) -> list[KalaTransaction]:
        """Get transaction history, sorted by timestamp."""
        return sorted(self.transactions, key=lambda t: t.timestamp)

    def to_dict(self) -> Dict[str, any]:
        """Serialize to dictionary."""
        return {
            "account_id": self.account_id,
            "counter": self.counter.to_dict(),
            "transactions": [
                {
                    "transaction_id": t.transaction_id,
                    "timestamp": t.timestamp,
                    "amount": t.amount,
                    "transaction_type": t.transaction_type,
                    "reason": t.reason,
                    "node_id": t.node_id
                }
                for t in self.transactions
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'CRDTKalaAccount':
        """Deserialize from dictionary."""
        account = cls(
            account_id=data["account_id"],
            node_id=data["counter"]["node_id"]
        )
        account.counter = PNCounter.from_dict(data["counter"])
        account.transactions = [
            KalaTransaction(**t) for t in data["transactions"]
        ]
        return account

    def __repr__(self) -> str:
        return (
            f"CRDTKalaAccount(account={self.account_id}, "
            f"balance={self.balance()}, "
            f"transactions={len(self.transactions)})"
        )
