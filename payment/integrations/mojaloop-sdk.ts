/**
 * Mojaloop SDK Integration
 *
 * Wrapper for official Mojaloop SDK implementing FSPIOP protocol.
 * Handles instant, low-fee transfers between DFSPs in Hawaii.
 *
 * Docs: https://docs.mojaloop.io/
 */

import axios, { AxiosInstance } from 'axios';
import { randomUUID } from 'crypto';

// ============================================================================
// Types
// ============================================================================

export interface MojaloopConfig {
  switchUrl: string;              // e.g., 'https://mojaloop.hawaii.gov'
  participantId: string;          // DFSP identifier (e.g., 'vessels-dfsp')
  apiKey: string;                 // Authentication key
  callbackUrl: string;            // Where Mojaloop sends callbacks
  timeoutMs?: number;             // Default: 30000
}

export interface QuoteParams {
  quoteId?: string;               // Optional, will generate if not provided
  transactionId: string;          // Idempotency key
  payerFspId: string;             // Source DFSP
  payeeFspId: string;             // Destination DFSP
  amountType: 'SEND' | 'RECEIVE'; // What amount is fixed
  amount: string;                 // Amount in USD (decimal string)
  currency: 'USD';
  transactionType: 'TRANSFER';
  note?: string;
}

export interface QuoteResponse {
  quoteId: string;
  transferAmount: string;         // What will be sent
  payeeReceiveAmount: string;     // What payee receives
  fees: string;                   // Mojaloop fees (usually very low)
  ilpPacket: string;              // Payment packet
  condition: string;              // Crypto condition for 2-phase commit
  expiration: string;             // ISO timestamp
}

export interface TransferParams {
  transferId?: string;            // Optional, will generate if not provided
  quoteId: string;                // From quote response
  payerFspId: string;
  payeeFspId: string;
  amount: string;
  currency: 'USD';
  ilpPacket: string;              // From quote response
  condition: string;              // From quote response
}

export interface TransferResponse {
  transferId: string;
  transferState: 'RECEIVED' | 'RESERVED' | 'COMMITTED' | 'ABORTED';
  completedTimestamp?: string;
  fulfilment?: string;            // Proof of completion
}

export interface CommitParams {
  transferId: string;
  fulfilment: string;             // Crypto fulfilment
}

// ============================================================================
// Mojaloop SDK
// ============================================================================

export class MojaloopSDK {
  private client: AxiosInstance;
  private config: MojaloopConfig;

  constructor(config: MojaloopConfig) {
    this.config = {
      timeoutMs: 30000,
      ...config,
    };

    this.client = axios.create({
      baseURL: this.config.switchUrl,
      timeout: this.config.timeoutMs,
      headers: {
        'Content-Type': 'application/vnd.interoperability.quotes+json;version=1.1',
        'FSPIOP-Source': this.config.participantId,
        'Authorization': `Bearer ${this.config.apiKey}`,
        'Date': new Date().toUTCString(),
      },
    });
  }

  /**
   * Request a quote for a transfer
   *
   * Phase 1 of Mojaloop 2-phase commit:
   * 1. Request quote → get fees and crypto condition
   * 2. Prepare transfer → reserve funds
   * 3. Commit transfer → complete or abort
   */
  async requestQuote(params: QuoteParams): Promise<QuoteResponse> {
    const quoteId = params.quoteId || randomUUID();

    try {
      const response = await this.client.post('/quotes', {
        quoteId,
        transactionId: params.transactionId,
        payer: {
          partyIdInfo: {
            partyIdType: 'FSPID',
            partyIdentifier: params.payerFspId,
          },
        },
        payee: {
          partyIdInfo: {
            partyIdType: 'FSPID',
            partyIdentifier: params.payeeFspId,
          },
        },
        amountType: params.amountType,
        amount: {
          amount: params.amount,
          currency: params.currency,
        },
        transactionType: {
          scenario: params.transactionType,
          initiator: 'PAYER',
          initiatorType: 'BUSINESS',
        },
        note: params.note,
      }, {
        headers: {
          'FSPIOP-Destination': params.payeeFspId,
        },
      });

      // Mojaloop responds asynchronously via callback
      // This is a synchronous wrapper - in production, implement webhook handler
      return {
        quoteId,
        transferAmount: response.data.transferAmount.amount,
        payeeReceiveAmount: response.data.payeeReceiveAmount.amount,
        fees: response.data.fees?.amount || '0',
        ilpPacket: response.data.ilpPacket,
        condition: response.data.condition,
        expiration: response.data.expiration,
      };
    } catch (error: any) {
      throw new MojaloopError(
        'QUOTE_FAILED',
        `Failed to request quote: ${error.message}`,
        error.response?.status === 408 || error.code === 'ECONNABORTED'
      );
    }
  }

  /**
   * Prepare a transfer (reserves funds)
   *
   * Phase 2 of Mojaloop 2-phase commit.
   * Funds are reserved but not yet moved.
   */
  async prepareTransfer(params: TransferParams): Promise<TransferResponse> {
    const transferId = params.transferId || randomUUID();

    try {
      const response = await this.client.post('/transfers', {
        transferId,
        payerFsp: params.payerFspId,
        payeeFsp: params.payeeFspId,
        amount: {
          amount: params.amount,
          currency: params.currency,
        },
        ilpPacket: params.ilpPacket,
        condition: params.condition,
        expiration: new Date(Date.now() + 30000).toISOString(), // 30s expiry
      }, {
        headers: {
          'FSPIOP-Destination': params.payeeFspId,
        },
      });

      return {
        transferId,
        transferState: response.data.transferState || 'RECEIVED',
        completedTimestamp: response.data.completedTimestamp,
        fulfilment: response.data.fulfilment,
      };
    } catch (error: any) {
      throw new MojaloopError(
        'TRANSFER_PREPARE_FAILED',
        `Failed to prepare transfer: ${error.message}`,
        error.response?.status === 408 || error.code === 'ECONNABORTED'
      );
    }
  }

  /**
   * Commit a transfer (completes the payment)
   *
   * Phase 3 of Mojaloop 2-phase commit.
   * Provide fulfilment to complete or abort to cancel.
   */
  async commitTransfer(params: CommitParams): Promise<void> {
    try {
      await this.client.put(`/transfers/${params.transferId}`, {
        fulfilment: params.fulfilment,
        completedTimestamp: new Date().toISOString(),
        transferState: 'COMMITTED',
      });
    } catch (error: any) {
      throw new MojaloopError(
        'TRANSFER_COMMIT_FAILED',
        `Failed to commit transfer: ${error.message}`,
        error.response?.status === 408 || error.code === 'ECONNABORTED'
      );
    }
  }

  /**
   * Abort a transfer (cancels the payment)
   */
  async abortTransfer(transferId: string, errorCode: string = 'TRANSFER_EXPIRED'): Promise<void> {
    try {
      await this.client.put(`/transfers/${transferId}/error`, {
        errorInformation: {
          errorCode,
          errorDescription: 'Transfer cancelled',
        },
      });
    } catch (error: any) {
      throw new MojaloopError(
        'TRANSFER_ABORT_FAILED',
        `Failed to abort transfer: ${error.message}`,
        false // Don't retry aborts
      );
    }
  }

  /**
   * Health check - verify connectivity to Mojaloop switch
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.client.get('/health');
      return true;
    } catch {
      return false;
    }
  }
}

// ============================================================================
// Error Handling
// ============================================================================

export class MojaloopError extends Error {
  constructor(
    public code: string,
    message: string,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = 'MojaloopError';
  }
}

// ============================================================================
// Helper: Retry with exponential backoff
// ============================================================================

export async function withMojaloopRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelayMs: number = 1000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      const isRetryable = error instanceof MojaloopError && error.retryable;

      if (attempt === maxRetries || !isRetryable) {
        throw error;
      }

      const delay = baseDelayMs * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw new Error('Max retries exceeded');
}
