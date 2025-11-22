"""
Payment Gateway Client

Bridges Python commercial agents with TypeScript payment infrastructure.
Communicates with the Vessels Payment Platform GraphQL API.
"""

import logging
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PayoutType(str, Enum):
    """Payout type options"""
    SLOW_FREE = "SLOW_FREE"
    FAST_FEE = "FAST_FEE"


class PayoutStatus(str, Enum):
    """Payout status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class PayoutQuote:
    """Payout quote details"""
    amount: float
    fee: float
    net_to_vendor: float
    estimated_delivery: str


@dataclass
class PayoutResult:
    """Result of payout request"""
    id: str
    amount: float
    fee: float
    net_to_vendor: float
    status: PayoutStatus
    requested_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class PaymentGatewayClient:
    """
    Client for communicating with TypeScript payment service.

    Handles:
    - Vendor payout requests
    - Gift card operations
    - Tax filing coordination
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        api_token: Optional[str] = None
    ):
        """
        Initialize payment gateway client.

        Args:
            base_url: Base URL of payment service (default: http://localhost:3000)
            api_token: JWT token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.graphql_endpoint = f"{self.base_url}/graphql"
        self.api_token = api_token
        self.session = requests.Session()

        if api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            })

        logger.info(f"Payment Gateway Client initialized: {self.base_url}")

    def set_token(self, token: str):
        """Update authentication token"""
        self.api_token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })

    def _execute_graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute GraphQL query.

        Args:
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            Response data

        Raises:
            Exception: If request fails
        """
        payload = {'query': query}
        if variables:
            payload['variables'] = variables

        try:
            response = self.session.post(
                self.graphql_endpoint,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if 'errors' in data:
                error_msg = data['errors'][0]['message']
                error_code = data['errors'][0].get('extensions', {}).get('code', 'UNKNOWN')
                raise Exception(f"GraphQL error ({error_code}): {error_msg}")

            return data.get('data', {})

        except requests.RequestException as e:
            logger.error(f"Payment service request failed: {e}")
            raise Exception(f"Payment service unavailable: {e}")

    def get_payout_quote(
        self,
        amount_usd: float,
        payout_type: PayoutType = PayoutType.SLOW_FREE
    ) -> PayoutQuote:
        """
        Get quote for payout.

        Args:
            amount_usd: Payout amount in USD
            payout_type: Type of payout (SLOW_FREE or FAST_FEE)

        Returns:
            PayoutQuote with fee and net amount
        """
        query = """
        query PayoutQuote($amount: USD!, $type: PayoutType!) {
          payoutQuote(amountUsd: $amount, type: $type) {
            amount
            fee
            netToVendor
            estimatedDelivery
          }
        }
        """

        variables = {
            'amount': amount_usd,
            'type': payout_type.value
        }

        data = self._execute_graphql(query, variables)
        quote_data = data['payoutQuote']

        return PayoutQuote(
            amount=float(quote_data['amount']),
            fee=float(quote_data['fee']),
            net_to_vendor=float(quote_data['netToVendor']),
            estimated_delivery=quote_data['estimatedDelivery']
        )

    def request_payout(
        self,
        vendor_id: str,
        amount_usd: float,
        payout_type: PayoutType = PayoutType.SLOW_FREE
    ) -> PayoutResult:
        """
        Request payout for vendor.

        Args:
            vendor_id: Vendor ID
            amount_usd: Payout amount in USD
            payout_type: Type of payout

        Returns:
            PayoutResult with payout details
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
            completedAt
            errorMessage
          }
        }
        """

        variables = {
            'input': {
                'vendorId': vendor_id,
                'amountUsd': amount_usd,
                'payoutType': payout_type.value
            }
        }

        data = self._execute_graphql(mutation, variables)
        payout_data = data['requestPayout']

        return PayoutResult(
            id=payout_data['id'],
            amount=float(payout_data['amount']),
            fee=float(payout_data['fee']),
            net_to_vendor=float(payout_data['netToVendor']),
            status=PayoutStatus(payout_data['status']),
            requested_at=payout_data['requestedAt'],
            completed_at=payout_data.get('completedAt'),
            error_message=payout_data.get('errorMessage')
        )

    def get_payout_status(self, payout_id: str) -> PayoutResult:
        """
        Get status of payout.

        Args:
            payout_id: Payout ID

        Returns:
            PayoutResult with current status
        """
        query = """
        query GetPayout($id: ID!) {
          payout(id: $id) {
            id
            amount
            fee
            netToVendor
            status
            requestedAt
            completedAt
            errorMessage
          }
        }
        """

        variables = {'id': payout_id}

        data = self._execute_graphql(query, variables)
        payout_data = data['payout']

        if not payout_data:
            raise Exception(f"Payout {payout_id} not found")

        return PayoutResult(
            id=payout_data['id'],
            amount=float(payout_data['amount']),
            fee=float(payout_data['fee']),
            net_to_vendor=float(payout_data['netToVendor']),
            status=PayoutStatus(payout_data['status']),
            requested_at=payout_data['requestedAt'],
            completed_at=payout_data.get('completedAt'),
            error_message=payout_data.get('errorMessage')
        )

    def get_vendor_balance(self, vendor_id: str) -> Dict[str, float]:
        """
        Get vendor balances.

        Args:
            vendor_id: Vendor ID

        Returns:
            Dictionary with earnings, tax_reserve, and kala balances
        """
        query = """
        query GetVendor($id: ID!) {
          vendor(id: $id) {
            earnings {
              usd
            }
            taxReserve {
              usd
            }
            kala {
              kala
            }
          }
        }
        """

        variables = {'id': vendor_id}

        data = self._execute_graphql(query, variables)
        vendor_data = data['vendor']

        if not vendor_data:
            raise Exception(f"Vendor {vendor_id} not found")

        return {
            'earnings_usd': float(vendor_data['earnings']['usd'] or 0),
            'tax_reserve_usd': float(vendor_data['taxReserve']['usd'] or 0),
            'kala': int(vendor_data['kala']['kala'] or 0)
        }

    def charge(
        self,
        company_id: str,
        amount: float,
        description: str
    ) -> Dict[str, Any]:
        """
        Charge company for referral fee.

        This is a simplified interface for the fee processor.
        In production, this would integrate with the gift card redemption flow.

        Args:
            company_id: Company/vendor ID to charge
            amount: Amount to charge
            description: Description of charge

        Returns:
            Result dictionary with success status
        """
        try:
            # For now, we simulate a successful charge
            # In production, this would:
            # 1. Verify vendor has sufficient balance
            # 2. Create a transaction record
            # 3. Update vendor's earnings and tax reserve

            logger.info(
                f"Processing charge: {company_id} - ${amount:.2f} - {description}"
            )

            # Get current balance to verify funds
            balance = self.get_vendor_balance(company_id)

            if balance['earnings_usd'] < amount:
                return {
                    'success': False,
                    'error': f"Insufficient balance: ${balance['earnings_usd']:.2f} < ${amount:.2f}"
                }

            # In production: Create debit transaction
            # For now, we just return success
            return {
                'success': True,
                'transaction_id': f"txn_{company_id}_{int(amount*100)}",
                'amount': amount,
                'description': description
            }

        except Exception as e:
            logger.error(f"Charge failed: {e}")
            return {
                'success': False,
                'error': str(e)
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
            transaction_id: Transaction ID to refund
            amount: Amount to refund
            reason: Reason for refund

        Returns:
            Result dictionary with success status
        """
        try:
            logger.info(
                f"Processing refund: {transaction_id} - ${amount:.2f} - {reason}"
            )

            # In production: Create credit transaction
            return {
                'success': True,
                'refund_id': f"refund_{transaction_id}",
                'amount': amount,
                'reason': reason
            }

        except Exception as e:
            logger.error(f"Refund failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
