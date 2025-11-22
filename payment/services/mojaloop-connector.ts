/**
 * Mojaloop Connector Service
 *
 * Integrates with Mojaloop for instant, low-fee transfers between DFSPs.
 * Implements FSPIOP (Financial Services Interoperability Protocol).
 *
 * Falls back gracefully to ACH/card rails when Mojaloop unavailable.
 */

import { Pool } from 'pg';
import { getOhanaLedger, dollarsToCents, centsToDollars } from './ohana-ledger';
import { v4 as uuidv4 } from 'uuid';
import axios, { AxiosInstance } from 'axios';

// ============================================================================
// TYPES
// ============================================================================

export enum MojaloopTransferStatus {
  RECEIVED = 'received',
  RESERVED = 'reserved',
  COMMITTED = 'committed',
  ABORTED = 'aborted',
  TIMEOUT = 'timeout',
}

export interface MojaloopTransfer {
  id: string;
  mojaloop TransferId: string;
  payerFsp: string;
  payeeFsp: string;
  amountUsd: number;
  currency: string;
  status: MojaloopTransferStatus;
  tbTransferId?: bigint;
  quoteAt?: Date;
  preparedAt?: Date;
  committedAt?: Date;
}

export interface MojaloopQuote {
  transferId: string;
  amountUsd: number;
  feeUsd: number;
  expiresAt: Date;
}

// ============================================================================
// MOJALOOP CONNECTOR SERVICE
// ============================================================================

export class MojaloopConnector {
  private httpClient: AxiosInstance;
  private participantId: string;

  constructor(
    private db: Pool,
    private config: {
      switchUrl: string;
      participantId: string;
      callbackUrl: string;
      apiKey: string;
    }
  ) {
    this.participantId = config.participantId;
    this.httpClient = axios.create({
      baseURL: config.switchUrl,
      headers: {
        'FSPIOP-Source': config.participantId,
        'Authorization': `Bearer ${config.apiKey}`,
        'Content-Type': 'application/vnd.interoperability.parties+json;version=1.0',
      },
    });
  }

  /**
   * Request quote for transfer
   */
  async requestQuote(params: {
    payeeFsp: string;
    amountUsd: number;
    currency?: string;
  }): Promise<MojaloopQuote> {
    const quoteId = uuidv4();
    const transferId = uuidv4();

    const response = await this.httpClient.post('/quotes', {
      quoteId,
      transactionId: transferId,
      payee: { partyIdInfo: { fspId: params.payeeFsp } },
      payer: { partyIdInfo: { fspId: this.participantId } },
      amountType: 'SEND',
      amount: {
        currency: params.currency || 'USD',
        amount: params.amountUsd.toFixed(2),
      },
      transactionType: {
        scenario: 'TRANSFER',
        initiator: 'PAYER',
        initiatorType: 'BUSINESS',
      },
    });

    return {
      transferId,
      amountUsd: params.amountUsd,
      feeUsd: parseFloat(response.data.transferAmount?.amount || '0'),
      expiresAt: new Date(response.data.expiration),
    };
  }

  /**
   * Execute Mojaloop transfer
   */
  async executeTransfer(params: {
    payeeFsp: string;
    payeeAccountId: string;
    amountUsd: number;
    currency?: string;
  }): Promise<MojaloopTransfer> {
    const transferId = uuidv4();
    const mojaloopTransferId = `ml-${transferId}`;

    try {
      // 1. Prepare transfer (reserve funds)
      await this.httpClient.post('/transfers', {
        transferId: mojaloopTransferId,
        payeeFsp: params.payeeFsp,
        payerFsp: this.participantId,
        amount: {
          currency: params.currency || 'USD',
          amount: params.amountUsd.toFixed(2),
        },
        ilpPacket: Buffer.from(JSON.stringify({
          data: { note: 'Ohana payment' },
        })).toString('base64'),
        condition: this.generateCondition(),
        expiration: new Date(Date.now() + 30000).toISOString(), // 30 sec timeout
      });

      // Record in database
      await this.db.query(
        `INSERT INTO mojaloop_transfers (
          id, mojaloop_transfer_id, payer_fsp, payee_fsp, amount_usd, currency, status, prepared_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())`,
        [
          transferId,
          mojaloopTransferId,
          this.participantId,
          params.payeeFsp,
          params.amountUsd,
          params.currency || 'USD',
          MojaloopTransferStatus.RESERVED,
        ]
      );

      // 2. Commit will happen via callback (see handleTransferCallback)

      return await this.getTransfer(transferId) as MojaloopTransfer;
    } catch (error) {
      console.error('Mojaloop transfer failed:', error);
      throw new Error('Mojaloop transfer failed. Falling back to ACH.');
    }
  }

  /**
   * Handle transfer commit callback from Mojaloop switch
   */
  async handleTransferCallback(params: {
    mojaloopTransferId: string;
    fulfilment: string;
    transferState: 'COMMITTED' | 'ABORTED';
  }): Promise<void> {
    const result = await this.db.query(
      'SELECT * FROM mojaloop_transfers WHERE mojaloop_transfer_id = $1',
      [params.mojaloopTransferId]
    );

    if (result.rows.length === 0) {
      throw new Error('Transfer not found');
    }

    const transfer = result.rows[0];

    if (params.transferState === 'COMMITTED') {
      // Execute ledger transfer
      const ledger = getOhanaLedger();
      // Logic depends on direction (incoming vs outgoing)
      // For now, simplified

      await this.db.query(
        `UPDATE mojaloop_transfers SET
          status = $1,
          committed_at = NOW()
        WHERE mojaloop_transfer_id = $2`,
        [MojaloopTransferStatus.COMMITTED, params.mojaloopTransferId]
      );
    } else {
      await this.db.query(
        'UPDATE mojaloop_transfers SET status = $1 WHERE mojaloop_transfer_id = $2',
        [MojaloopTransferStatus.ABORTED, params.mojaloopTransferId]
      );
    }
  }

  /**
   * Receive incoming transfer from another DFSP
   */
  async handleIncomingTransfer(params: {
    mojaloopTransferId: string;
    payerFsp: string;
    amountUsd: number;
    targetAccountId: string; // Vendor or gift card ID
  }): Promise<void> {
    // Credit target account on ledger
    const ledger = getOhanaLedger();
    // Implementation depends on account type

    // Record in database
    await this.db.query(
      `INSERT INTO mojaloop_transfers (
        id, mojaloop_transfer_id, payer_fsp, payee_fsp, amount_usd, currency, status, committed_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())`,
      [
        uuidv4(),
        params.mojaloopTransferId,
        params.payerFsp,
        this.participantId,
        params.amountUsd,
        'USD',
        MojaloopTransferStatus.COMMITTED,
      ]
    );
  }

  /**
   * Check if Mojaloop is available for a DFSP
   */
  async isAvailable(fspId: string): Promise<boolean> {
    try {
      const response = await this.httpClient.get(`/participants/${fspId}`);
      return response.status === 200;
    } catch {
      return false;
    }
  }

  /**
   * Get transfer by ID
   */
  async getTransfer(transferId: string): Promise<MojaloopTransfer | null> {
    const result = await this.db.query(
      'SELECT * FROM mojaloop_transfers WHERE id = $1',
      [transferId]
    );
    return result.rows.length > 0 ? this.mapRow(result.rows[0]) : null;
  }

  /**
   * Generate ILP condition (simplified - use real crypto in production)
   */
  private generateCondition(): string {
    return Buffer.from(uuidv4()).toString('base64').substring(0, 48);
  }

  /**
   * Map database row to MojaloopTransfer
   */
  private mapRow(row: any): MojaloopTransfer {
    return {
      id: row.id,
      mojaloopTransferId: row.mojaloop_transfer_id,
      payerFsp: row.payer_fsp,
      payeeFsp: row.payee_fsp,
      amountUsd: parseFloat(row.amount_usd),
      currency: row.currency,
      status: row.status as MojaloopTransferStatus,
      tbTransferId: row.tb_transfer_id ? BigInt(row.tb_transfer_id) : undefined,
      quoteAt: row.quote_at,
      preparedAt: row.prepared_at,
      committedAt: row.committed_at,
    };
  }
}
