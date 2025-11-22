/**
 * Tax Orchestrator Service
 *
 * Automates Hawaii GET (General Excise Tax) filing and payment.
 * Default rate: 4.5% (4% state + 0.5% county surcharge)
 */

import { Pool } from 'pg';
import { getOhanaLedger, dollarsToCents, centsToDollars } from './ohana-ledger';
import { v4 as uuidv4 } from 'uuid';

// ============================================================================
// TYPES
// ============================================================================

export enum FilingFrequency {
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly',
  SEMIANNUAL = 'semiannual',
  ANNUAL = 'annual',
}

export enum FilingStatus {
  SCHEDULED = 'scheduled',
  PROCESSING = 'processing',
  FILED = 'filed',
  FAILED = 'failed',
  AMENDED = 'amended',
}

export interface TaxFiling {
  id: string;
  vendorId: string;
  filingPeriodStart: Date;
  filingPeriodEnd: Date;
  filingFrequency: FilingFrequency;
  grossReceiptsUsd: number;
  getRate: number;
  getDueUsd: number;
  status: FilingStatus;
  tbTransferId?: bigint;
  htoConfirmationNumber?: string;
  htoFiledAt?: Date;
  dueDate: Date;
  scheduledAt: Date;
  filedAt?: Date;
  errorMessage?: string;
}

// ============================================================================
// TAX ORCHESTRATOR SERVICE
// ============================================================================

export class TaxOrchestrator {
  constructor(
    private db: Pool,
    private htoIntegration: HawaiiTaxOnlineIntegration
  ) {}

  /**
   * Calculate GET summary for vendor period
   */
  async calculateGETForPeriod(
    vendorId: string,
    periodStart: Date,
    periodEnd: Date
  ): Promise<{ grossReceipts: number; getDue: number }> {
    // Sum all redemptions during period
    const result = await this.db.query(
      `SELECT COALESCE(SUM(amount_usd), 0) as total
       FROM gift_card_transactions
       WHERE vendor_id = $1
         AND transaction_type = 'redemption'
         AND created_at >= $2
         AND created_at < $3`,
      [vendorId, periodStart, periodEnd]
    );

    const grossReceipts = parseFloat(result.rows[0].total);

    // Get vendor's GET rate
    const vendorResult = await this.db.query(
      'SELECT get_rate FROM vendors WHERE id = $1',
      [vendorId]
    );
    const getRate = parseFloat(vendorResult.rows[0].get_rate);

    const getDue = grossReceipts * getRate;

    return {
      grossReceipts,
      getDue,
    };
  }

  /**
   * Schedule tax filing for vendor
   */
  async scheduleFiling(params: {
    vendorId: string;
    periodStart: Date;
    periodEnd: Date;
    dueDate: Date;
    filingFrequency: FilingFrequency;
  }): Promise<TaxFiling> {
    // Calculate GET due
    const { grossReceipts, getDue } = await this.calculateGETForPeriod(
      params.vendorId,
      params.periodStart,
      params.periodEnd
    );

    // Get vendor GET rate
    const vendorResult = await this.db.query(
      'SELECT get_rate FROM vendors WHERE id = $1',
      [params.vendorId]
    );
    const getRate = parseFloat(vendorResult.rows[0].get_rate);

    // Create filing record
    const filingId = uuidv4();
    const result = await this.db.query(
      `INSERT INTO tax_filings (
        id, vendor_id, filing_period_start, filing_period_end, filing_frequency,
        gross_receipts_usd, get_rate, get_due_usd, status, due_date
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      RETURNING *`,
      [
        filingId,
        params.vendorId,
        params.periodStart,
        params.periodEnd,
        params.filingFrequency,
        grossReceipts,
        getRate,
        getDue,
        FilingStatus.SCHEDULED,
        params.dueDate,
      ]
    );

    return this.mapRow(result.rows[0]);
  }

  /**
   * File and pay GET (automated)
   */
  async fileAndPayGET(filingId: string): Promise<TaxFiling> {
    const filing = await this.getFiling(filingId);
    if (!filing) {
      throw new Error('Filing not found');
    }

    if (filing.status !== FilingStatus.SCHEDULED) {
      throw new Error(`Filing status is ${filing.status}, cannot file`);
    }

    // Update status to processing
    await this.db.query(
      'UPDATE tax_filings SET status = $1 WHERE id = $2',
      [FilingStatus.PROCESSING, filingId]
    );

    try {
      // 1. Execute ledger transfer (tax reserve → bank bridge)
      const ledger = getOhanaLedger();
      const { transferId } = await ledger.payGET(
        filing.vendorId,
        dollarsToCents(filing.getDueUsd)
      );

      // 2. File with Hawaii Tax Online
      const htoResult = await this.htoIntegration.fileGET({
        vendorId: filing.vendorId,
        periodStart: filing.filingPeriodStart,
        periodEnd: filing.filingPeriodEnd,
        grossReceipts: filing.grossReceiptsUsd,
        getDue: filing.getDueUsd,
      });

      // 3. Initiate payment to HTO
      await this.htoIntegration.payGET({
        vendorId: filing.vendorId,
        amountUsd: filing.getDueUsd,
        confirmationNumber: htoResult.confirmationNumber,
      });

      // Update filing record
      await this.db.query(
        `UPDATE tax_filings SET
          status = $1,
          tb_transfer_id = $2,
          hto_confirmation_number = $3,
          hto_filed_at = NOW(),
          filed_at = NOW()
        WHERE id = $4`,
        [
          FilingStatus.FILED,
          transferId.toString(),
          htoResult.confirmationNumber,
          filingId,
        ]
      );

      return await this.getFiling(filingId) as TaxFiling;
    } catch (error) {
      await this.db.query(
        'UPDATE tax_filings SET status = $1, error_message = $2 WHERE id = $3',
        [FilingStatus.FAILED, (error as Error).message, filingId]
      );
      throw error;
    }
  }

  /**
   * Process scheduled filings (called by cron job)
   */
  async processScheduledFilings(lookAheadDays: number = 3): Promise<number> {
    const lookAheadDate = new Date();
    lookAheadDate.setDate(lookAheadDate.getDate() + lookAheadDays);

    const result = await this.db.query(
      `SELECT * FROM tax_filings
       WHERE status = $1 AND due_date <= $2
       ORDER BY due_date ASC`,
      [FilingStatus.SCHEDULED, lookAheadDate.toISOString()]
    );

    let processed = 0;
    for (const row of result.rows) {
      try {
        await this.fileAndPayGET(row.id);
        processed++;
      } catch (error) {
        console.error(`Failed to file ${row.id}:`, error);
      }
    }

    return processed;
  }

  /**
   * Get filing by ID
   */
  async getFiling(filingId: string): Promise<TaxFiling | null> {
    const result = await this.db.query(
      'SELECT * FROM tax_filings WHERE id = $1',
      [filingId]
    );
    return result.rows.length > 0 ? this.mapRow(result.rows[0]) : null;
  }

  /**
   * Get vendor filing history
   */
  async getVendorFilings(vendorId: string, limit: number = 12): Promise<TaxFiling[]> {
    const result = await this.db.query(
      `SELECT * FROM tax_filings
       WHERE vendor_id = $1
       ORDER BY filing_period_end DESC
       LIMIT $2`,
      [vendorId, limit]
    );
    return result.rows.map(row => this.mapRow(row));
  }

  /**
   * Map database row to TaxFiling
   */
  private mapRow(row: any): TaxFiling {
    return {
      id: row.id,
      vendorId: row.vendor_id,
      filingPeriodStart: row.filing_period_start,
      filingPeriodEnd: row.filing_period_end,
      filingFrequency: row.filing_frequency as FilingFrequency,
      grossReceiptsUsd: parseFloat(row.gross_receipts_usd),
      getRate: parseFloat(row.get_rate),
      getDueUsd: parseFloat(row.get_due_usd),
      status: row.status as FilingStatus,
      tbTransferId: row.tb_transfer_id ? BigInt(row.tb_transfer_id) : undefined,
      htoConfirmationNumber: row.hto_confirmation_number,
      htoFiledAt: row.hto_filed_at,
      dueDate: row.due_date,
      scheduledAt: row.scheduled_at,
      filedAt: row.filed_at,
      errorMessage: row.error_message,
    };
  }
}

// ============================================================================
// HAWAII TAX ONLINE INTEGRATION INTERFACE
// ============================================================================

export interface HawaiiTaxOnlineIntegration {
  /**
   * File GET return with HTO
   */
  fileGET(params: {
    vendorId: string;
    periodStart: Date;
    periodEnd: Date;
    grossReceipts: number;
    getDue: number;
  }): Promise<{ confirmationNumber: string }>;

  /**
   * Pay GET via ACH debit from tax reserve account
   */
  payGET(params: {
    vendorId: string;
    amountUsd: number;
    confirmationNumber: string;
  }): Promise<{ transactionId: string }>;
}
