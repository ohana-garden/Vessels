/**
 * Gift Card Service
 *
 * Manages Ohana Gift Cards as a closed-loop prepaid system.
 * FinCEN compliant: ≤$2,000 daily load limit, no cash access except HI law <$5.
 */

import { Pool } from 'pg';
import { getOhanaLedger, dollarsToCents, centsToDollars } from './ohana-ledger';
import { v4 as uuidv4 } from 'uuid';
import { randomBytes } from 'crypto';

// ============================================================================
// TYPES
// ============================================================================

export enum GiftCardStatus {
  PENDING_ACTIVATION = 'pending_activation',
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  DEPLETED = 'depleted',
  EXPIRED = 'expired',
}

export interface GiftCard {
  id: string;
  cardNumber: string;
  cardToken: string;
  ownerActorId?: string;
  donorActorId?: string;
  status: GiftCardStatus;
  currentBalanceUsd: number;
  originalBalanceUsd: number;
  dailyLoadLimitUsd: number;
  tbLiabilityAccountId: bigint;
  issuedAt?: Date;
  activatedAt?: Date;
  expiresAt?: Date;
  lastUsedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface GiftCardTransaction {
  id: string;
  giftCardId: string;
  transactionType: 'load' | 'redemption' | 'cashout' | 'refund';
  amountUsd: number;
  vendorId?: string;
  tbTransferId: bigint;
  locationDescription?: string;
  createdAt: Date;
}

// ============================================================================
// GIFT CARD SERVICE
// ============================================================================

export class GiftCardService {
  constructor(private db: Pool) {}

  /**
   * Issue a new gift card
   */
  async issueCard(params: {
    initialBalanceUsd: number;
    donorActorId: string;
    ownerActorId?: string;
    expiresAt?: Date;
  }): Promise<GiftCard> {
    const cardId = uuidv4();
    const cardToken = this.generateCardToken();

    // Create TigerBeetle account
    const ledger = getOhanaLedger();
    const { liability } = await ledger.createGiftCard(cardId);

    // Load initial balance if provided
    if (params.initialBalanceUsd > 0) {
      await ledger.loadGiftCard(cardId, dollarsToCents(params.initialBalanceUsd));
    }

    // Insert into PostgreSQL
    const result = await this.db.query(
      `INSERT INTO gift_cards (
        id, card_number, card_token, owner_actor_id, donor_actor_id,
        status, current_balance_usd, original_balance_usd, tb_liability_account_id,
        issued_at, expires_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), $10)
      RETURNING *`,
      [
        cardId,
        `OHANA-${cardToken}`,
        cardToken,
        params.ownerActorId || params.donorActorId,
        params.donorActorId,
        GiftCardStatus.ACTIVE,
        params.initialBalanceUsd,
        params.initialBalanceUsd,
        liability.toString(),
        params.expiresAt,
      ]
    );

    return this.mapRow(result.rows[0]);
  }

  /**
   * Load money onto gift card (enforce $2,000 daily limit)
   */
  async loadCard(
    cardToken: string,
    amountUsd: number,
    donorActorId?: string
  ): Promise<GiftCardTransaction> {
    // Validate amount
    if (amountUsd <= 0 || amountUsd > 2000) {
      throw new Error('Load amount must be between $0.01 and $2,000');
    }

    const card = await this.getCardByToken(cardToken);
    if (!card) {
      throw new Error('Gift card not found');
    }

    if (card.status !== GiftCardStatus.ACTIVE) {
      throw new Error(`Card status is ${card.status}, cannot load`);
    }

    // Check daily load limit
    await this.enforceDailyLoadLimit(card.id, amountUsd);

    // Load on TigerBeetle
    const ledger = getOhanaLedger();
    const { transferId } = await ledger.loadGiftCard(
      card.id,
      dollarsToCents(amountUsd)
    );

    // Update PostgreSQL
    await this.db.query(
      `UPDATE gift_cards SET
        current_balance_usd = current_balance_usd + $1,
        updated_at = NOW()
      WHERE id = $2`,
      [amountUsd, card.id]
    );

    // Record transaction
    const txn = await this.recordTransaction({
      giftCardId: card.id,
      transactionType: 'load',
      amountUsd,
      tbTransferId: transferId,
    });

    // Update daily load tracking
    await this.updateDailyLoad(card.id, amountUsd);

    return txn;
  }

  /**
   * Redeem card at vendor (split into earnings + GET)
   */
  async redeemCard(params: {
    cardToken: string;
    vendorId: string;
    amountUsd: number;
    getRate?: number;
    locationDescription?: string;
  }): Promise<GiftCardTransaction> {
    const card = await this.getCardByToken(params.cardToken);
    if (!card) {
      throw new Error('Gift card not found');
    }

    if (card.status !== GiftCardStatus.ACTIVE) {
      throw new Error(`Card status is ${card.status}, cannot redeem`);
    }

    if (params.amountUsd > card.currentBalanceUsd) {
      throw new Error('Insufficient card balance');
    }

    // Redeem on TigerBeetle
    const ledger = getOhanaLedger();
    const { transferIds } = await ledger.redeemGiftCard(
      card.id,
      params.vendorId,
      dollarsToCents(params.amountUsd),
      params.getRate || 0.045
    );

    // Update PostgreSQL
    const newBalance = card.currentBalanceUsd - params.amountUsd;
    await this.db.query(
      `UPDATE gift_cards SET
        current_balance_usd = $1,
        last_used_at = NOW(),
        status = CASE WHEN $1 = 0 THEN 'depleted'::gift_card_status ELSE status END,
        updated_at = NOW()
      WHERE id = $2`,
      [newBalance, card.id]
    );

    // Record transaction
    return await this.recordTransaction({
      giftCardId: card.id,
      transactionType: 'redemption',
      amountUsd: params.amountUsd,
      vendorId: params.vendorId,
      tbTransferId: transferIds[0],
      locationDescription: params.locationDescription,
    });
  }

  /**
   * Cash out card balance <$5 (Hawaii law)
   */
  async cashOutCard(cardToken: string): Promise<GiftCardTransaction> {
    const card = await this.getCardByToken(cardToken);
    if (!card) {
      throw new Error('Gift card not found');
    }

    if (card.currentBalanceUsd >= 5.00) {
      throw new Error('Cash out only allowed for balances less than $5');
    }

    if (card.currentBalanceUsd === 0) {
      throw new Error('Card balance is zero');
    }

    // Cash out on TigerBeetle
    const ledger = getOhanaLedger();
    const { transferId } = await ledger.cashOutGiftCard(
      card.id,
      dollarsToCents(card.currentBalanceUsd)
    );

    // Update PostgreSQL
    await this.db.query(
      `UPDATE gift_cards SET
        current_balance_usd = 0,
        status = 'depleted',
        updated_at = NOW()
      WHERE id = $1`,
      [card.id]
    );

    // Record transaction
    return await this.recordTransaction({
      giftCardId: card.id,
      transactionType: 'cashout',
      amountUsd: card.currentBalanceUsd,
      tbTransferId: transferId,
    });
  }

  /**
   * Get card by token
   */
  async getCardByToken(cardToken: string): Promise<GiftCard | null> {
    const result = await this.db.query(
      'SELECT * FROM gift_cards WHERE card_token = $1',
      [cardToken]
    );
    return result.rows.length > 0 ? this.mapRow(result.rows[0]) : null;
  }

  /**
   * Get card balance (from TigerBeetle for accuracy)
   */
  async getCardBalance(cardToken: string): Promise<number> {
    const card = await this.getCardByToken(cardToken);
    if (!card) {
      throw new Error('Gift card not found');
    }

    const ledger = getOhanaLedger();
    const balanceCents = await ledger.getGiftCardBalance(card.id);
    return centsToDollars(balanceCents);
  }

  /**
   * Enforce $2,000 daily load limit per card (FinCEN compliance)
   */
  private async enforceDailyLoadLimit(cardId: string, amountUsd: number): Promise<void> {
    const today = new Date().toISOString().split('T')[0];

    const result = await this.db.query(
      `SELECT total_loaded_usd FROM gift_card_daily_loads
       WHERE gift_card_id = $1 AND load_date = $2`,
      [cardId, today]
    );

    const totalLoaded = result.rows.length > 0 ? parseFloat(result.rows[0].total_loaded_usd) : 0;

    if (totalLoaded + amountUsd > 2000) {
      throw new Error(
        `Daily load limit exceeded. Already loaded $${totalLoaded.toFixed(2)} today. ` +
        `Limit is $2,000 per day.`
      );
    }
  }

  /**
   * Update daily load tracking
   */
  private async updateDailyLoad(cardId: string, amountUsd: number): Promise<void> {
    const today = new Date().toISOString().split('T')[0];

    await this.db.query(
      `INSERT INTO gift_card_daily_loads (gift_card_id, load_date, total_loaded_usd, load_count)
       VALUES ($1, $2, $3, 1)
       ON CONFLICT (gift_card_id, load_date)
       DO UPDATE SET
         total_loaded_usd = gift_card_daily_loads.total_loaded_usd + $3,
         load_count = gift_card_daily_loads.load_count + 1`,
      [cardId, today, amountUsd]
    );
  }

  /**
   * Record transaction in PostgreSQL
   */
  private async recordTransaction(params: {
    giftCardId: string;
    transactionType: 'load' | 'redemption' | 'cashout' | 'refund';
    amountUsd: number;
    vendorId?: string;
    tbTransferId: bigint;
    locationDescription?: string;
  }): Promise<GiftCardTransaction> {
    const result = await this.db.query(
      `INSERT INTO gift_card_transactions (
        id, gift_card_id, transaction_type, amount_usd, vendor_id,
        tb_transfer_id, location_description
      ) VALUES ($1, $2, $3, $4, $5, $6, $7)
      RETURNING *`,
      [
        uuidv4(),
        params.giftCardId,
        params.transactionType,
        params.amountUsd,
        params.vendorId,
        params.tbTransferId.toString(),
        params.locationDescription,
      ]
    );

    return this.mapTransactionRow(result.rows[0]);
  }

  /**
   * Generate random card token
   */
  private generateCardToken(): string {
    return randomBytes(8).toString('hex').toUpperCase();
  }

  /**
   * Map database row to GiftCard
   */
  private mapRow(row: any): GiftCard {
    return {
      id: row.id,
      cardNumber: row.card_number,
      cardToken: row.card_token,
      ownerActorId: row.owner_actor_id,
      donorActorId: row.donor_actor_id,
      status: row.status as GiftCardStatus,
      currentBalanceUsd: parseFloat(row.current_balance_usd),
      originalBalanceUsd: parseFloat(row.original_balance_usd),
      dailyLoadLimitUsd: parseFloat(row.daily_load_limit_usd),
      tbLiabilityAccountId: BigInt(row.tb_liability_account_id),
      issuedAt: row.issued_at,
      activatedAt: row.activated_at,
      expiresAt: row.expires_at,
      lastUsedAt: row.last_used_at,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }

  /**
   * Map database row to GiftCardTransaction
   */
  private mapTransactionRow(row: any): GiftCardTransaction {
    return {
      id: row.id,
      giftCardId: row.gift_card_id,
      transactionType: row.transaction_type,
      amountUsd: parseFloat(row.amount_usd),
      vendorId: row.vendor_id,
      tbTransferId: BigInt(row.tb_transfer_id),
      locationDescription: row.location_description,
      createdAt: row.created_at,
    };
  }
}
