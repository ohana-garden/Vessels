/**
 * Payout Orchestrator Service
 *
 * Manages vendor payouts via multiple rails:
 * - Slow (free): Standard ACH, scheduled batches
 * - Fast (fee): RTP/FedNow/Push-to-debit, instant
 */

import { Pool } from 'pg';
import { getOhanaLedger, dollarsToCents, centsToDollars } from './ohana-ledger';
import { v4 as uuidv4 } from 'uuid';

// ============================================================================
// TYPES
// ============================================================================

export enum PayoutType {
  SLOW_FREE = 'slow_free',
  FAST_FEE = 'fast_fee',
}

export enum PayoutStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum PayoutRail {
  ACH_STANDARD = 'ach_standard',
  ACH_SAME_DAY = 'ach_same_day',
  RTP = 'rtp',
  FEDNOW = 'fednow',
  PUSH_TO_DEBIT = 'push_to_debit',
}

export interface Payout {
  id: string;
  vendorId: string;
  payoutType: PayoutType;
  amountUsd: number;
  feeUsd: number;
  netToVendorUsd: number;
  payoutRail: PayoutRail;
  railCostUsd: number;
  status: PayoutStatus;
  tbTransferId?: bigint;
  externalProvider?: string;
  externalTransactionId?: string;
  requestedAt: Date;
  processedAt?: Date;
  completedAt?: Date;
  errorMessage?: string;
}

export interface PayoutQuote {
  amountUsd: number;
  feeUsd: number;
  netToVendorUsd: number;
  estimatedDelivery: string;
  rail: PayoutRail;
}

// ============================================================================
// PAYOUT ORCHESTRATOR SERVICE
// ============================================================================

export class PayoutOrchestrator {
  constructor(
    private db: Pool,
    private achProvider: ACHProvider,
    private rtpProvider: RTPProvider,
    private cardProcessor: CardProcessor
  ) {}

  /**
   * Get payout quote (slow vs fast)
   */
  async getQuote(vendorId: string, amountUsd: number, type: PayoutType): Promise<PayoutQuote> {
    if (type === PayoutType.SLOW_FREE) {
      return {
        amountUsd,
        feeUsd: 0,
        netToVendorUsd: amountUsd,
        estimatedDelivery: '2-3 business days',
        rail: PayoutRail.ACH_STANDARD,
      };
    } else {
      // Fast payout: 1% or $0.50 minimum
      const feeUsd = Math.max(amountUsd * 0.01, 0.50);
      const netUsd = amountUsd - feeUsd;

      return {
        amountUsd,
        feeUsd,
        netToVendorUsd: netUsd,
        estimatedDelivery: 'Instant (< 1 minute)',
        rail: PayoutRail.PUSH_TO_DEBIT,
      };
    }
  }

  /**
   * Request vendor payout
   */
  async requestPayout(params: {
    vendorId: string;
    amountUsd: number;
    payoutType: PayoutType;
  }): Promise<Payout> {
    // Validate vendor balance
    const ledger = getOhanaLedger();
    const balances = await ledger.getVendorBalances(params.vendorId);
    if (balances.earnings < dollarsToCents(params.amountUsd)) {
      throw new Error('Insufficient vendor earnings balance');
    }

    // Get quote
    const quote = await this.getQuote(params.vendorId, params.amountUsd, params.payoutType);

    // Create payout record
    const payoutId = uuidv4();
    const result = await this.db.query(
      `INSERT INTO payouts (
        id, vendor_id, payout_type, amount_usd, fee_usd, net_to_vendor_usd,
        payout_rail, rail_cost_usd, status
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
      RETURNING *`,
      [
        payoutId,
        params.vendorId,
        params.payoutType,
        params.amountUsd,
        quote.feeUsd,
        quote.netToVendorUsd,
        quote.rail,
        0, // Will update after processing
        PayoutStatus.PENDING,
      ]
    );

    // Process immediately or schedule
    if (params.payoutType === PayoutType.FAST_FEE) {
      await this.processFastPayout(payoutId);
    }
    // Slow payouts are processed by batch job

    return this.mapRow(result.rows[0]);
  }

  /**
   * Process fast payout immediately
   */
  private async processFastPayout(payoutId: string): Promise<void> {
    const payout = await this.getPayout(payoutId);
    if (!payout) {
      throw new Error('Payout not found');
    }

    await this.db.query(
      'UPDATE payouts SET status = $1, processed_at = NOW() WHERE id = $2',
      [PayoutStatus.PROCESSING, payoutId]
    );

    try {
      // Execute ledger transfer
      const ledger = getOhanaLedger();
      const { transferIds } = await ledger.processFastPayout(
        payout.vendorId,
        dollarsToCents(payout.amountUsd),
        dollarsToCents(payout.feeUsd)
      );

      // Execute external payout via card processor
      const externalResult = await this.cardProcessor.pushToDebit({
        vendorId: payout.vendorId,
        amountUsd: payout.netToVendorUsd,
        idempotencyKey: payoutId,
      });

      // Update payout record
      await this.db.query(
        `UPDATE payouts SET
          status = $1,
          tb_transfer_id = $2,
          external_provider = $3,
          external_transaction_id = $4,
          rail_cost_usd = $5,
          completed_at = NOW()
        WHERE id = $6`,
        [
          PayoutStatus.COMPLETED,
          transferIds[0].toString(),
          'card_processor',
          externalResult.transactionId,
          externalResult.costUsd,
          payoutId,
        ]
      );
    } catch (error) {
      await this.db.query(
        'UPDATE payouts SET status = $1, error_message = $2 WHERE id = $3',
        [PayoutStatus.FAILED, (error as Error).message, payoutId]
      );
      throw error;
    }
  }

  /**
   * Process slow payouts in batch (called by scheduled job)
   */
  async processSlowPayoutBatch(limit: number = 100): Promise<number> {
    // Get pending slow payouts
    const result = await this.db.query(
      `SELECT * FROM payouts
       WHERE payout_type = $1 AND status = $2
       ORDER BY requested_at ASC
       LIMIT $3`,
      [PayoutType.SLOW_FREE, PayoutStatus.PENDING, limit]
    );

    let processed = 0;
    for (const row of result.rows) {
      try {
        await this.processSlowPayout(row.id);
        processed++;
      } catch (error) {
        console.error(`Failed to process payout ${row.id}:`, error);
      }
    }

    return processed;
  }

  /**
   * Process single slow payout
   */
  private async processSlowPayout(payoutId: string): Promise<void> {
    const payout = await this.getPayout(payoutId);
    if (!payout) {
      throw new Error('Payout not found');
    }

    await this.db.query(
      'UPDATE payouts SET status = $1, processed_at = NOW() WHERE id = $2',
      [PayoutStatus.PROCESSING, payoutId]
    );

    try {
      // Execute ledger transfer
      const ledger = getOhanaLedger();
      const { transferId } = await ledger.processSlowPayout(
        payout.vendorId,
        dollarsToCents(payout.amountUsd)
      );

      // Execute external ACH
      const externalResult = await this.achProvider.initiateCredit({
        vendorId: payout.vendorId,
        amountUsd: payout.amountUsd,
        idempotencyKey: payoutId,
      });

      // Update payout record
      await this.db.query(
        `UPDATE payouts SET
          status = $1,
          tb_transfer_id = $2,
          external_provider = $3,
          external_transaction_id = $4,
          rail_cost_usd = $5,
          completed_at = NOW()
        WHERE id = $6`,
        [
          PayoutStatus.COMPLETED,
          transferId.toString(),
          'ach_provider',
          externalResult.transactionId,
          externalResult.costUsd,
          payoutId,
        ]
      );
    } catch (error) {
      await this.db.query(
        'UPDATE payouts SET status = $1, error_message = $2 WHERE id = $3',
        [PayoutStatus.FAILED, (error as Error).message, payoutId]
      );
      throw error;
    }
  }

  /**
   * Get payout by ID
   */
  async getPayout(payoutId: string): Promise<Payout | null> {
    const result = await this.db.query('SELECT * FROM payouts WHERE id = $1', [payoutId]);
    return result.rows.length > 0 ? this.mapRow(result.rows[0]) : null;
  }

  /**
   * Get vendor payout history
   */
  async getVendorPayouts(vendorId: string, limit: number = 50): Promise<Payout[]> {
    const result = await this.db.query(
      'SELECT * FROM payouts WHERE vendor_id = $1 ORDER BY requested_at DESC LIMIT $2',
      [vendorId, limit]
    );
    return result.rows.map(row => this.mapRow(row));
  }

  /**
   * Map database row to Payout
   */
  private mapRow(row: any): Payout {
    return {
      id: row.id,
      vendorId: row.vendor_id,
      payoutType: row.payout_type as PayoutType,
      amountUsd: parseFloat(row.amount_usd),
      feeUsd: parseFloat(row.fee_usd),
      netToVendorUsd: parseFloat(row.net_to_vendor_usd),
      payoutRail: row.payout_rail as PayoutRail,
      railCostUsd: parseFloat(row.rail_cost_usd),
      status: row.status as PayoutStatus,
      tbTransferId: row.tb_transfer_id ? BigInt(row.tb_transfer_id) : undefined,
      externalProvider: row.external_provider,
      externalTransactionId: row.external_transaction_id,
      requestedAt: row.requested_at,
      processedAt: row.processed_at,
      completedAt: row.completed_at,
      errorMessage: row.error_message,
    };
  }
}

// ============================================================================
// EXTERNAL PROVIDER INTERFACES
// ============================================================================

export interface ACHProvider {
  initiateCredit(params: {
    vendorId: string;
    amountUsd: number;
    idempotencyKey: string;
  }): Promise<{ transactionId: string; costUsd: number }>;
}

export interface RTPProvider {
  sendPayment(params: {
    vendorId: string;
    amountUsd: number;
    idempotencyKey: string;
  }): Promise<{ transactionId: string; costUsd: number }>;
}

export interface CardProcessor {
  pushToDebit(params: {
    vendorId: string;
    amountUsd: number;
    idempotencyKey: string;
  }): Promise<{ transactionId: string; costUsd: number }>;
}
