/**
 * RTP/FedNow Provider Integration
 *
 * Real-time payment processing for instant vendor payouts.
 * Supports both RTP (The Clearing House) and FedNow (Federal Reserve).
 *
 * Features:
 * - Instant settlement (< 20 seconds)
 * - 24/7/365 availability
 * - Higher fees than ACH (~$0.045 per transaction + basis points)
 * - Push-to-debit for instant delivery
 *
 * Providers:
 * - Modern Treasury (RTP + FedNow aggregator)
 * - The Clearing House (direct RTP)
 * - Federal Reserve (direct FedNow)
 */

import axios, { AxiosInstance } from 'axios';
import { randomUUID } from 'crypto';

// ============================================================================
// Types
// ============================================================================

export interface RTPProviderConfig {
  provider: 'modern_treasury' | 'clearing_house' | 'federal_reserve';
  apiUrl: string;
  apiKey: string;
  organizationId?: string;        // For Modern Treasury
  network?: 'rtp' | 'fednow';     // Preferred network
  timeoutMs?: number;
}

export interface RTPPaymentParams {
  vendorId: string;               // Internal vendor ID
  accountNumber: string;          // Destination account
  routingNumber: string;          // Destination routing (ABA)
  amount: number;                 // USD amount
  memo?: string;
  idempotencyKey?: string;
}

export interface RTPPaymentResult {
  transactionId: string;          // Provider transaction ID
  status: 'sent' | 'completed' | 'failed' | 'returned';
  amount: number;
  fees: number;                   // Provider fees in USD
  network: 'rtp' | 'fednow';      // Which network was used
  completedAt?: Date;
  errorCode?: string;
  errorMessage?: string;
}

export interface RTPReturnInfo {
  returnCode: string;             // R01, R02, etc.
  returnReason: string;
  returnedAt: Date;
}

// ============================================================================
// RTP Provider Implementation
// ============================================================================

export class RTPProvider {
  private client: AxiosInstance;
  private config: RTPProviderConfig;

  constructor(config: RTPProviderConfig) {
    this.config = {
      network: 'rtp',
      timeoutMs: 60000,             // RTP can take up to 60s
      ...config,
    };

    this.client = axios.create({
      baseURL: this.config.apiUrl,
      timeout: this.config.timeoutMs,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config.apiKey}`,
      },
    });
  }

  /**
   * Send instant payment via RTP or FedNow
   */
  async sendPayment(params: RTPPaymentParams): Promise<RTPPaymentResult> {
    const idempotencyKey = params.idempotencyKey || randomUUID();

    try {
      // Route to appropriate provider
      switch (this.config.provider) {
        case 'modern_treasury':
          return await this.sendViaModernTreasury(params, idempotencyKey);
        case 'clearing_house':
          return await this.sendViaClearingHouse(params, idempotencyKey);
        case 'federal_reserve':
          return await this.sendViaFedNow(params, idempotencyKey);
        default:
          throw new RTPError('INVALID_PROVIDER', `Unknown provider: ${this.config.provider}`);
      }
    } catch (error: any) {
      if (error instanceof RTPError) {
        throw error;
      }

      throw new RTPError(
        'RTP_SEND_FAILED',
        `Failed to send RTP payment: ${error.message}`,
        error.response?.status === 408 || error.code === 'ECONNABORTED'
      );
    }
  }

  /**
   * Send via Modern Treasury (multi-network aggregator)
   */
  private async sendViaModernTreasury(
    params: RTPPaymentParams,
    idempotencyKey: string
  ): Promise<RTPPaymentResult> {
    const response = await this.client.post('/api/payment_orders', {
      type: 'rtp',
      subtype: this.config.network,
      amount: Math.round(params.amount * 100), // Convert to cents
      direction: 'credit',
      currency: 'USD',
      receiving_account: {
        account_number: params.accountNumber,
        routing_number: params.routingNumber,
      },
      description: params.memo || `Vessels payout to ${params.vendorId}`,
      metadata: {
        vendor_id: params.vendorId,
      },
    }, {
      headers: {
        'Idempotency-Key': idempotencyKey,
      },
    });

    const data = response.data;

    // Calculate fees (Modern Treasury pricing: $0.045 + 0.1%)
    const fees = 0.045 + (params.amount * 0.001);

    return {
      transactionId: data.id,
      status: this.mapModernTreasuryStatus(data.status),
      amount: params.amount,
      fees,
      network: this.config.network!,
      completedAt: data.completed_at ? new Date(data.completed_at) : undefined,
    };
  }

  /**
   * Send via The Clearing House (direct RTP)
   */
  private async sendViaClearingHouse(
    params: RTPPaymentParams,
    idempotencyKey: string
  ): Promise<RTPPaymentResult> {
    const response = await this.client.post('/v1/payments', {
      EndToEndId: idempotencyKey,
      Amount: {
        Currency: 'USD',
        Value: params.amount.toFixed(2),
      },
      Debtor: {
        Name: 'Vessels Platform',
        Account: {
          Identification: process.env.RTP_DEBTOR_ACCOUNT,
        },
      },
      Creditor: {
        Name: `Vendor ${params.vendorId}`,
        Account: {
          Identification: params.accountNumber,
          SchemeName: 'BBAN',
        },
      },
      RemittanceInformation: {
        Unstructured: params.memo || 'Vendor payout',
      },
    });

    const data = response.data;

    return {
      transactionId: data.PaymentId,
      status: data.Status === 'ACCP' ? 'completed' : 'sent',
      amount: params.amount,
      fees: 0.045, // TCH base fee
      network: 'rtp',
      completedAt: data.CompletionTime ? new Date(data.CompletionTime) : undefined,
    };
  }

  /**
   * Send via FedNow (direct Federal Reserve)
   */
  private async sendViaFedNow(
    params: RTPPaymentParams,
    idempotencyKey: string
  ): Promise<RTPPaymentResult> {
    const response = await this.client.post('/fednow/v1/payments', {
      messageId: idempotencyKey,
      amount: {
        currency: 'USD',
        value: params.amount,
      },
      debtorAccount: {
        identification: process.env.FEDNOW_DEBTOR_ACCOUNT,
      },
      creditorAccount: {
        identification: params.accountNumber,
        routingNumber: params.routingNumber,
      },
      remittanceInformation: params.memo || 'Vendor payout',
    });

    const data = response.data;

    return {
      transactionId: data.paymentId,
      status: data.status === 'ACCEPTED' ? 'completed' : 'sent',
      amount: params.amount,
      fees: 0.01, // FedNow is cheaper: $0.01 per transaction
      network: 'fednow',
      completedAt: data.settlementTime ? new Date(data.settlementTime) : undefined,
    };
  }

  /**
   * Get payment status
   */
  async getPaymentStatus(transactionId: string): Promise<RTPPaymentResult> {
    try {
      let endpoint: string;

      switch (this.config.provider) {
        case 'modern_treasury':
          endpoint = `/api/payment_orders/${transactionId}`;
          break;
        case 'clearing_house':
          endpoint = `/v1/payments/${transactionId}`;
          break;
        case 'federal_reserve':
          endpoint = `/fednow/v1/payments/${transactionId}`;
          break;
        default:
          throw new RTPError('INVALID_PROVIDER', `Unknown provider: ${this.config.provider}`);
      }

      const response = await this.client.get(endpoint);
      const data = response.data;

      return {
        transactionId: data.id || data.PaymentId || data.paymentId,
        status: this.mapStatus(data),
        amount: this.extractAmount(data),
        fees: this.calculateFees(this.extractAmount(data)),
        network: this.config.network!,
        completedAt: this.extractCompletedAt(data),
      };
    } catch (error: any) {
      throw new RTPError(
        'STATUS_CHECK_FAILED',
        `Failed to check payment status: ${error.message}`,
        true
      );
    }
  }

  /**
   * Check if routing number supports RTP/FedNow
   */
  async checkNetworkSupport(routingNumber: string): Promise<{
    rtp: boolean;
    fednow: boolean;
  }> {
    try {
      const response = await this.client.get('/api/routing_details', {
        params: { routing_number: routingNumber },
      });

      return {
        rtp: response.data.supports_rtp || false,
        fednow: response.data.supports_fednow || false,
      };
    } catch {
      // If lookup fails, assume not supported
      return { rtp: false, fednow: false };
    }
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.client.get('/health');
      return true;
    } catch {
      return false;
    }
  }

  // ============================================================================
  // Private Helpers
  // ============================================================================

  private mapModernTreasuryStatus(status: string): RTPPaymentResult['status'] {
    switch (status) {
      case 'approved':
      case 'completed':
        return 'completed';
      case 'returned':
        return 'returned';
      case 'failed':
        return 'failed';
      default:
        return 'sent';
    }
  }

  private mapStatus(data: any): RTPPaymentResult['status'] {
    // Provider-specific status mapping
    if (data.status === 'completed' || data.Status === 'ACCP' || data.status === 'ACCEPTED') {
      return 'completed';
    }
    if (data.status === 'returned' || data.Status === 'RJCT') {
      return 'returned';
    }
    if (data.status === 'failed') {
      return 'failed';
    }
    return 'sent';
  }

  private extractAmount(data: any): number {
    if (data.amount) {
      return typeof data.amount === 'number' ? data.amount / 100 : parseFloat(data.amount);
    }
    if (data.Amount?.Value) {
      return parseFloat(data.Amount.Value);
    }
    return 0;
  }

  private extractCompletedAt(data: any): Date | undefined {
    if (data.completed_at) return new Date(data.completed_at);
    if (data.CompletionTime) return new Date(data.CompletionTime);
    if (data.settlementTime) return new Date(data.settlementTime);
    return undefined;
  }

  private calculateFees(amount: number): number {
    // Modern Treasury: $0.045 + 0.1%
    // FedNow: $0.01 flat
    // RTP: $0.045 flat
    if (this.config.provider === 'modern_treasury') {
      return 0.045 + (amount * 0.001);
    }
    if (this.config.network === 'fednow') {
      return 0.01;
    }
    return 0.045;
  }
}

// ============================================================================
// Error Handling
// ============================================================================

export class RTPError extends Error {
  constructor(
    public code: string,
    message: string,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = 'RTPError';
  }
}

// ============================================================================
// Helper: Retry with exponential backoff
// ============================================================================

export async function withRTPRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelayMs: number = 2000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      const isRetryable = error instanceof RTPError && error.retryable;

      if (attempt === maxRetries || !isRetryable) {
        throw error;
      }

      const delay = baseDelayMs * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw new Error('Max retries exceeded');
}
