"""
Payment Gateway Client

Integrates the Python commercial fee processor with the TypeScript payment ledger.
Handles GraphQL API calls, authentication, retries, and graceful degradation.
"""

import os
import logging
import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class PaymentOperationStatus(str, Enum):
    """Status of payment operation"""
    SUCCESS = "success"
    FAILED = "failed"
    QUEUED = "queued"
    RETRYING = "retrying"


@dataclass
class QueuedTransaction:
    """Transaction queued for retry when payment service is unavailable"""
    transaction_id: str
    operation_type: str
    payload: Dict[str, Any]
    queued_at: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    max_retries: int = 5
    last_error: Optional[str] = None


class SystemIntervention(Exception):
    """
    Critical exception raised when system intervention is required.

    Used for scenarios like:
    - Repeated payment failures
    - Service unavailability beyond thresholds
    - Dead letter queue overflow
    """
    pass


class PaymentGatewayClient:
    """
    Client for interacting with the Vessels Payment Platform (GraphQL API).

    Features:
    - GraphQL query/mutation execution
    - JWT Bearer token authentication
    - Automatic retries with exponential backoff
    - Local transaction queueing when service is down
    - Dead letter queue for permanently failed transactions
    """

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        timeout: int = 10,
        enable_local_queue: bool = True
    ):
        """
        Initialize payment gateway client.

        Args:
            api_base_url: Base URL for payment API (default: from env PAYMENT_API_URL)
            api_key: JWT token for authentication (default: from env PAYMENT_API_KEY)
            max_retries: Maximum number of retry attempts
            retry_backoff_factor: Backoff factor for retries (seconds)
            timeout: Request timeout in seconds
            enable_local_queue: Enable local queueing when service is down
        """
        # Load configuration from environment
        self.api_base_url = api_base_url or os.environ.get(
            "PAYMENT_API_URL",
            "http://payment-service:3000/graphql"
        )
        self.api_key = api_key or os.environ.get("PAYMENT_API_KEY")

        if not self.api_key:
            logger.warning(
                "PAYMENT_API_KEY not set. Payment operations will fail without authentication."
            )

        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.timeout = timeout
        self.enable_local_queue = enable_local_queue

        # Configure HTTP session with retry logic
        self.session = self._create_session()

        # Local transaction queue for graceful degradation
        self.queued_transactions: List[QueuedTransaction] = []
        self.dead_letter_queue: List[QueuedTransaction] = []

        logger.info(
            f"PaymentGatewayClient initialized: {self.api_base_url}, "
            f"retries={max_retries}, queue_enabled={enable_local_queue}"
        )

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry configuration."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def _execute_graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query or mutation.

        Args:
            query: GraphQL query/mutation string
            variables: Query variables
            operation_name: Optional operation name

        Returns:
            Response data dict

        Raises:
            requests.RequestException: On network/HTTP errors
            ValueError: On GraphQL errors
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }

        if operation_name:
            payload["operationName"] = operation_name

        try:
            response = self.session.post(
                self.api_base_url,
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()

            # Check for GraphQL errors
            if "errors" in result:
                error_messages = [e.get("message", str(e)) for e in result["errors"]]
                raise ValueError(f"GraphQL errors: {'; '.join(error_messages)}")

            return result.get("data", {})

        except requests.RequestException as e:
            logger.error(f"GraphQL request failed: {e}")
            raise

    def charge_company(
        self,
        company_id: str,
        amount: float,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Charge a company for referral fees.

        Note: This is a logical operation that may map to different underlying
        payment mechanisms (gift card issuance, direct charge, etc.)

        Args:
            company_id: Company identifier
            amount: Amount in USD
            description: Transaction description
            metadata: Optional metadata

        Returns:
            Result dict with 'success' bool and optional 'error' string
        """
        try:
            # For now, we'll create a placeholder transaction
            # In production, this would map to the appropriate payment mechanism
            # (e.g., issue gift card, direct ACH charge, etc.)

            logger.info(
                f"Charging company {company_id}: ${amount:.2f} - {description}"
            )

            # TODO: Implement actual charge mechanism
            # This could be:
            # 1. Issue gift card to company's account
            # 2. Direct charge via ACH/card
            # 3. Invoice generation

            # For now, simulate successful charge
            return {
                "success": True,
                "transaction_id": f"charge_{company_id}_{int(time.time())}",
                "amount": amount,
                "description": description
            }

        except Exception as e:
            logger.error(f"Failed to charge company {company_id}: {e}")

            # Queue for retry if local queue is enabled
            if self.enable_local_queue:
                self._queue_transaction(
                    operation_type="charge",
                    payload={
                        "company_id": company_id,
                        "amount": amount,
                        "description": description,
                        "metadata": metadata
                    }
                )

            return {
                "success": False,
                "error": str(e)
            }

    def redeem_gift_card(
        self,
        card_token: str,
        vendor_id: str,
        amount_usd: float,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Redeem a gift card at a vendor.

        Args:
            card_token: Gift card token
            vendor_id: Vendor ID
            amount_usd: Amount to redeem
            location: Optional location string

        Returns:
            Transaction data or error
        """
        mutation = """
        mutation RedeemGiftCard($input: RedeemGiftCardInput!) {
            redeemGiftCard(input: $input) {
                id
                amount
                vendor {
                    businessName
                }
                createdAt
            }
        }
        """

        variables = {
            "input": {
                "cardToken": card_token,
                "vendorId": vendor_id,
                "amountUsd": amount_usd,
                "location": location
            }
        }

        try:
            data = self._execute_graphql(mutation, variables)
            return {
                "success": True,
                "transaction": data.get("redeemGiftCard")
            }
        except Exception as e:
            logger.error(f"Failed to redeem gift card: {e}")

            if self.enable_local_queue:
                self._queue_transaction(
                    operation_type="redeem_gift_card",
                    payload={
                        "card_token": card_token,
                        "vendor_id": vendor_id,
                        "amount_usd": amount_usd,
                        "location": location
                    }
                )

            return {
                "success": False,
                "error": str(e)
            }

    def request_payout(
        self,
        vendor_id: str,
        amount_usd: float,
        payout_type: str = "SLOW_FREE"
    ) -> Dict[str, Any]:
        """
        Request vendor payout.

        Args:
            vendor_id: Vendor ID
            amount_usd: Amount to payout
            payout_type: "SLOW_FREE" or "FAST_FEE"

        Returns:
            Payout data or error
        """
        mutation = """
        mutation RequestPayout($input: RequestPayoutInput!) {
            requestPayout(input: $input) {
                id
                amount
                fee
                netToVendor
                status
                requestedAt
            }
        }
        """

        variables = {
            "input": {
                "vendorId": vendor_id,
                "amountUsd": amount_usd,
                "payoutType": payout_type
            }
        }

        try:
            data = self._execute_graphql(mutation, variables)
            return {
                "success": True,
                "payout": data.get("requestPayout")
            }
        except Exception as e:
            logger.error(f"Failed to request payout: {e}")

            if self.enable_local_queue:
                self._queue_transaction(
                    operation_type="request_payout",
                    payload={
                        "vendor_id": vendor_id,
                        "amount_usd": amount_usd,
                        "payout_type": payout_type
                    }
                )

            return {
                "success": False,
                "error": str(e)
            }

    def refund(
        self,
        transaction_id: str,
        amount: float,
        reason: str
    ) -> Dict[str, Any]:
        """
        Refund a transaction.

        Args:
            transaction_id: Original transaction ID
            amount: Amount to refund
            reason: Refund reason

        Returns:
            Result dict with 'success' bool and optional 'error' string
        """
        try:
            # TODO: Implement actual refund mechanism via GraphQL
            logger.info(
                f"Refunding transaction {transaction_id}: ${amount:.2f} - {reason}"
            )

            # Placeholder implementation
            return {
                "success": True,
                "refund_id": f"refund_{transaction_id}_{int(time.time())}",
                "amount": amount,
                "reason": reason
            }

        except Exception as e:
            logger.error(f"Failed to refund transaction {transaction_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _queue_transaction(
        self,
        operation_type: str,
        payload: Dict[str, Any]
    ):
        """Queue a transaction for retry when service is unavailable."""
        transaction_id = f"queued_{operation_type}_{int(time.time())}"

        queued = QueuedTransaction(
            transaction_id=transaction_id,
            operation_type=operation_type,
            payload=payload
        )

        self.queued_transactions.append(queued)

        logger.warning(
            f"Transaction queued for retry: {transaction_id} "
            f"(queue size: {len(self.queued_transactions)})"
        )

        # Check if queue is growing too large
        if len(self.queued_transactions) > 100:
            logger.critical(
                f"Transaction queue overflow: {len(self.queued_transactions)} items. "
                "System intervention may be required."
            )
            raise SystemIntervention(
                f"Transaction queue overflow: {len(self.queued_transactions)} items"
            )

    def process_queued_transactions(self) -> Dict[str, int]:
        """
        Attempt to process all queued transactions.

        Returns:
            Stats dict with 'succeeded', 'failed', 'still_queued' counts
        """
        if not self.queued_transactions:
            return {"succeeded": 0, "failed": 0, "still_queued": 0}

        stats = {"succeeded": 0, "failed": 0, "still_queued": 0}

        # Process a copy of the queue
        to_process = list(self.queued_transactions)
        self.queued_transactions.clear()

        for queued in to_process:
            try:
                # Retry the operation based on type
                if queued.operation_type == "charge":
                    result = self.charge_company(**queued.payload)
                elif queued.operation_type == "redeem_gift_card":
                    result = self.redeem_gift_card(**queued.payload)
                elif queued.operation_type == "request_payout":
                    result = self.request_payout(**queued.payload)
                else:
                    logger.error(f"Unknown operation type: {queued.operation_type}")
                    continue

                if result.get("success"):
                    stats["succeeded"] += 1
                    logger.info(f"Queued transaction succeeded: {queued.transaction_id}")
                else:
                    # Retry failed - check retry count
                    queued.retry_count += 1
                    queued.last_error = result.get("error")

                    if queued.retry_count >= queued.max_retries:
                        # Move to dead letter queue
                        self.dead_letter_queue.append(queued)
                        stats["failed"] += 1
                        logger.error(
                            f"Transaction moved to dead letter queue: {queued.transaction_id} "
                            f"after {queued.retry_count} retries"
                        )
                    else:
                        # Re-queue for another attempt
                        self.queued_transactions.append(queued)
                        stats["still_queued"] += 1

            except Exception as e:
                logger.error(f"Error processing queued transaction: {e}")
                queued.retry_count += 1
                queued.last_error = str(e)

                if queued.retry_count >= queued.max_retries:
                    self.dead_letter_queue.append(queued)
                    stats["failed"] += 1
                else:
                    self.queued_transactions.append(queued)
                    stats["still_queued"] += 1

        logger.info(
            f"Processed queued transactions: "
            f"{stats['succeeded']} succeeded, "
            f"{stats['failed']} failed, "
            f"{stats['still_queued']} still queued"
        )

        return stats

    def get_queue_stats(self) -> Dict[str, int]:
        """Get statistics about transaction queues."""
        return {
            "queued": len(self.queued_transactions),
            "dead_letter": len(self.dead_letter_queue)
        }

    def health_check(self) -> bool:
        """
        Check if payment service is healthy.

        Returns:
            True if service is responding, False otherwise
        """
        try:
            # Simple query to test connectivity
            query = """
            query HealthCheck {
                __typename
            }
            """

            self._execute_graphql(query)
            return True

        except Exception as e:
            logger.warning(f"Payment service health check failed: {e}")
            return False

    # ========================================================================
    # NEW: TigerBeetle + Mojaloop + RTP Integration
    # ========================================================================

    def create_vendor_accounts(self, vendor_id: str, name: str) -> Dict[str, Any]:
        """
        Create vendor accounts in TigerBeetle ledger.

        Args:
            vendor_id: Unique vendor UUID
            name: Vendor display name

        Returns:
            Vendor data with account IDs
        """
        mutation = """
        mutation CreateVendor($vendorId: String!, $name: String!) {
            createVendor(vendorId: $vendorId, name: $name) {
                id
                name
                createdAt
            }
        }
        """

        try:
            data = self._execute_graphql(mutation, {"vendorId": vendor_id, "name": name})
            return {"success": True, "vendor": data.get("createVendor")}
        except Exception as e:
            logger.error(f"Failed to create vendor accounts: {e}")
            return {"success": False, "error": str(e)}

    def get_vendor_balance(
        self,
        vendor_id: str,
        account_type: str = "vendor_get_reserve"
    ) -> Dict[str, Any]:
        """
        Get vendor account balance from TigerBeetle.

        Args:
            vendor_id: Vendor UUID
            account_type: Account type (vendor_get_reserve, vendor_tax_reserve, vendor_kala)

        Returns:
            Balance data
        """
        query = """
        query GetBalance($vendorId: String!, $accountType: String!) {
            accountBalance(vendorId: $vendorId, accountType: $accountType) {
                vendorId
                accountType
                balanceUsd
                asOf
            }
        }
        """

        try:
            data = self._execute_graphql(query, {"vendorId": vendor_id, "accountType": account_type})
            balance_data = data.get("accountBalance", {})
            return {
                "success": True,
                "balance_usd": balance_data.get("balanceUsd", 0),
                "as_of": balance_data.get("asOf")
            }
        except Exception as e:
            logger.error(f"Failed to get vendor balance: {e}")
            return {"success": False, "error": str(e)}

    def transfer_vendor_to_vendor(
        self,
        from_vendor_id: str,
        to_vendor_id: str,
        amount_usd: float,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transfer funds between vendors using TigerBeetle.

        Args:
            from_vendor_id: Source vendor UUID
            to_vendor_id: Destination vendor UUID
            amount_usd: Amount in USD
            description: Optional transfer note

        Returns:
            Transfer result
        """
        mutation = """
        mutation Transfer(
            $fromVendorId: String!
            $toVendorId: String!
            $amountUsd: Float!
            $description: String
        ) {
            transfer(
                fromVendorId: $fromVendorId
                toVendorId: $toVendorId
                amountUsd: $amountUsd
                description: $description
            ) {
                transferId
                status
                amountUsd
            }
        }
        """

        try:
            data = self._execute_graphql(mutation, {
                "fromVendorId": from_vendor_id,
                "toVendorId": to_vendor_id,
                "amountUsd": amount_usd,
                "description": description
            })
            return {"success": True, "transfer": data.get("transfer")}
        except Exception as e:
            logger.error(f"Failed to transfer funds: {e}")
            return {"success": False, "error": str(e)}

    def payout_vendor(
        self,
        vendor_id: str,
        amount_usd: float,
        method: str = "ACH"
    ) -> Dict[str, Any]:
        """
        Send payout to vendor using ACH, RTP, Mojaloop, or Card.

        Args:
            vendor_id: Vendor UUID
            amount_usd: Amount in USD
            method: Payout method (ACH, RTP, MOJALOOP, CARD)

        Returns:
            Payout result with fees
        """
        mutation = """
        mutation Payout(
            $vendorId: String!
            $amountUsd: Float!
            $method: PayoutMethod!
        ) {
            payout(
                vendorId: $vendorId
                amountUsd: $amountUsd
                method: $method
            ) {
                payoutId
                status
                amountUsd
                feesUsd
            }
        }
        """

        try:
            data = self._execute_graphql(mutation, {
                "vendorId": vendor_id,
                "amountUsd": amount_usd,
                "method": method
            })
            payout_data = data.get("payout", {})
            return {
                "success": True,
                "payout_id": payout_data.get("payoutId"),
                "status": payout_data.get("status"),
                "amount_usd": payout_data.get("amountUsd"),
                "fees_usd": payout_data.get("feesUsd", 0)
            }
        except Exception as e:
            logger.error(f"Failed to send payout: {e}")

            # Queue for retry
            if self.enable_local_queue:
                self._queue_transaction(
                    operation_type="payout_vendor",
                    payload={
                        "vendor_id": vendor_id,
                        "amount_usd": amount_usd,
                        "method": method
                    }
                )

            return {"success": False, "error": str(e)}

    def get_transaction_history(
        self,
        vendor_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get transaction history for a vendor.

        Args:
            vendor_id: Vendor UUID
            limit: Maximum transactions to return

        Returns:
            Transaction list
        """
        query = """
        query TransactionHistory($vendorId: String!, $limit: Int) {
            transactionHistory(vendorId: $vendorId, limit: $limit) {
                id
                fromVendor
                toVendor
                amountUsd
                description
                timestamp
            }
        }
        """

        try:
            data = self._execute_graphql(query, {"vendorId": vendor_id, "limit": limit})
            return {
                "success": True,
                "transactions": data.get("transactionHistory", [])
            }
        except Exception as e:
            logger.error(f"Failed to get transaction history: {e}")
            return {"success": False, "error": str(e)}
