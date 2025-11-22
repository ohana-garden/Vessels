/**
 * Ohana Ledger Service
 *
 * High-level double-entry ledger service built on TigerBeetle.
 * Provides business logic layer for all money and Kala operations.
 *
 * Core principles:
 * - All money operations are atomic and idempotent
 * - USD and Kala are kept on separate ledgers (never mixed)
 * - Full audit trail for all transfers
 * - Strong consistency guarantees from TigerBeetle
 */

import { createClient, Client, Account, Transfer } from 'tigerbeetle-node';
import {
  Ledger,
  AccountType,
  TransferType,
  VendorAccountIds,
  GiftCardAccountIds,
  createVendorAccounts,
  createGiftCardAccount,
  createGiftCardLoadTransfer,
  createGiftCardRedemptionTransfers,
  createSlowPayoutTransfer,
  createFastPayoutTransfers,
  createTaxPaymentTransfer,
  createKalaAwardTransfer,
  generateTransferId,
  generateAccountId,
  calculateBalance,
  isLiability Account,
  handleAccountCreationError,
  handleTransferCreationError,
  AccountBalance,
} from '../models/tigerbeetle-schema';

// ============================================================================
// CONFIGURATION
// ============================================================================

export interface OhanaLedgerConfig {
  tigerbeetleClusterIds: number[];  // e.g., [0, 1, 2] for 3-node cluster
  tigerbeetleReplicas: string[];     // e.g., ['3000', '3001', '3002'] for ports
  communityOrgId: string;             // UUID of community fund organization
}

// ============================================================================
// OHANA LEDGER SERVICE
// ============================================================================

export class OhanaLedgerService {
  private client: Client;
  private config: OhanaLedgerConfig;
  private communityBankBridgeId: bigint;
  private kalaPoolId: bigint;
  private feesPayoutFastId: bigint;

  constructor(config: OhanaLedgerConfig) {
    this.config = config;

    // Initialize TigerBeetle client
    this.client = createClient({
      cluster_id: config.tigerbeetleClusterIds[0],
      replica_addresses: config.tigerbeetleReplicas,
    });

    // Generate system account IDs
    this.communityBankBridgeId = generateAccountId(
      config.communityOrgId,
      AccountType.COMMUNITY_BANK_BRIDGE,
      Ledger.USD
    );

    this.kalaPoolId = generateAccountId(
      config.communityOrgId,
      AccountType.KALA_POOL,
      Ledger.KALA
    );

    this.feesPayoutFastId = generateAccountId(
      config.communityOrgId,
      AccountType.FEES_PAYOUT_FAST,
      Ledger.USD
    );
  }

  /**
   * Initialize system accounts (run once on deployment)
   */
  async initializeSystemAccounts(): Promise<void> {
    const systemAccounts: Account[] = [
      // Community bank bridge (mirrors external bank balance)
      {
        id: this.communityBankBridgeId,
        debits_pending: 0n,
        debits_posted: 0n,
        credits_pending: 0n,
        credits_posted: 0n,
        user_data_128: 0n,
        user_data_64: 0n,
        user_data_32: 0,
        reserved: 0,
        ledger: Ledger.USD,
        code: AccountType.COMMUNITY_BANK_BRIDGE,
        flags: 0,
        timestamp: 0n,
      },
      // Kala pool for awarding participation
      {
        id: this.kalaPoolId,
        debits_pending: 0n,
        debits_posted: 0n,
        credits_pending: 0n,
        credits_posted: 1_000_000_000n, // Initialize with 1B Kala
        user_data_128: 0n,
        user_data_64: 0n,
        user_data_32: 0,
        reserved: 0,
        ledger: Ledger.KALA,
        code: AccountType.KALA_POOL,
        flags: 0,
        timestamp: 0n,
      },
      // Fast payout fees account
      {
        id: this.feesPayoutFastId,
        debits_pending: 0n,
        debits_posted: 0n,
        credits_pending: 0n,
        credits_posted: 0n,
        user_data_128: 0n,
        user_data_64: 0n,
        user_data_32: 0,
        reserved: 0,
        ledger: Ledger.USD,
        code: AccountType.FEES_PAYOUT_FAST,
        flags: 0,
        timestamp: 0n,
      },
    ];

    const errors = await this.client.createAccounts(systemAccounts);
    for (const error of errors) {
      // Ignore "exists" errors (idempotent initialization)
      if (error.result !== 0 && error.result !== 1) {
        throw new Error(
          `Failed to create system account: ${handleAccountCreationError(error.result)}`
        );
      }
    }
  }

  // ==========================================================================
  // VENDOR OPERATIONS
  // ==========================================================================

  /**
   * Create ledger accounts for a new vendor
   */
  async createVendor(vendorId: string): Promise<VendorAccountIds> {
    const { accounts, ids } = createVendorAccounts(vendorId);

    const errors = await this.client.createAccounts(accounts);
    for (const error of errors) {
      if (error.result !== 0) {
        throw new Error(
          `Failed to create vendor account: ${handleAccountCreationError(error.result)}`
        );
      }
    }

    return ids;
  }

  /**
   * Get vendor balances
   */
  async getVendorBalances(vendorId: string): Promise<{
    earnings: bigint;
    taxReserve: bigint;
    kala: bigint;
  }> {
    const earningsId = generateAccountId(vendorId, AccountType.VENDOR_EARNINGS, Ledger.USD);
    const taxReserveId = generateAccountId(vendorId, AccountType.VENDOR_TAX_RESERVE, Ledger.USD);
    const kalaId = generateAccountId(vendorId, AccountType.KALA_PARTICIPANT, Ledger.KALA);

    const accounts = await this.client.lookupAccounts([earningsId, taxReserveId, kalaId]);

    return {
      earnings: calculateBalance(accounts[0]),
      taxReserve: calculateBalance(accounts[1]),
      kala: calculateBalance(accounts[2]),
    };
  }

  // ==========================================================================
  // GIFT CARD OPERATIONS
  // ==========================================================================

  /**
   * Create ledger account for a new gift card
   */
  async createGiftCard(cardId: string, initialBalanceCents: bigint = 0n): Promise<GiftCardAccountIds> {
    const { account, ids } = createGiftCardAccount(cardId, initialBalanceCents);

    const errors = await this.client.createAccounts([account]);
    if (errors.length > 0 && errors[0].result !== 0) {
      throw new Error(
        `Failed to create gift card account: ${handleAccountCreationError(errors[0].result)}`
      );
    }

    return ids;
  }

  /**
   * Load money onto a gift card (donor purchase)
   */
  async loadGiftCard(
    cardId: string,
    amountCents: bigint,
    idempotencyKey?: string
  ): Promise<{ transferId: bigint }> {
    const giftCardLiabilityId = generateAccountId(
      cardId,
      AccountType.GIFT_CARD_LIABILITY,
      Ledger.USD
    );

    const transferId = idempotencyKey
      ? generateTransferIdFromReference(idempotencyKey)
      : generateTransferId();

    const transfer = createGiftCardLoadTransfer(
      transferId,
      this.communityBankBridgeId,
      giftCardLiabilityId,
      amountCents
    );

    const errors = await this.client.createTransfers([transfer]);
    if (errors.length > 0 && errors[0].result !== 0 && errors[0].result !== 1) {
      // Ignore exists error (idempotent)
      throw new Error(
        `Failed to load gift card: ${handleTransferCreationError(errors[0].result)}`
      );
    }

    return { transferId };
  }

  /**
   * Redeem gift card at vendor (split into earnings + GET)
   */
  async redeemGiftCard(
    cardId: string,
    vendorId: string,
    amountCents: bigint,
    getRate: number = 0.045,
    idempotencyKey?: string
  ): Promise<{ transferIds: bigint[] }> {
    const giftCardLiabilityId = generateAccountId(
      cardId,
      AccountType.GIFT_CARD_LIABILITY,
      Ledger.USD
    );
    const vendorEarningsId = generateAccountId(
      vendorId,
      AccountType.VENDOR_EARNINGS,
      Ledger.USD
    );
    const vendorTaxReserveId = generateAccountId(
      vendorId,
      AccountType.VENDOR_TAX_RESERVE,
      Ledger.USD
    );

    const baseTransferId = idempotencyKey
      ? generateTransferIdFromReference(idempotencyKey)
      : generateTransferId();

    const transfers = createGiftCardRedemptionTransfers(
      baseTransferId,
      giftCardLiabilityId,
      vendorEarningsId,
      vendorTaxReserveId,
      amountCents,
      getRate
    );

    const errors = await this.client.createTransfers(transfers);
    for (const error of errors) {
      if (error.result !== 0 && error.result !== 1) {
        throw new Error(
          `Failed to redeem gift card: ${handleTransferCreationError(error.result)}`
        );
      }
    }

    return { transferIds: transfers.map(t => t.id) };
  }

  /**
   * Get gift card balance
   */
  async getGiftCardBalance(cardId: string): Promise<bigint> {
    const liabilityId = generateAccountId(cardId, AccountType.GIFT_CARD_LIABILITY, Ledger.USD);
    const accounts = await this.client.lookupAccounts([liabilityId]);

    if (accounts.length === 0) {
      throw new Error(`Gift card not found: ${cardId}`);
    }

    // Liability account: credit balance = what we owe
    return calculateBalance(accounts[0], true);
  }

  /**
   * Cash out gift card (<$5 per Hawaii law)
   */
  async cashOutGiftCard(
    cardId: string,
    amountCents: bigint,
    idempotencyKey?: string
  ): Promise<{ transferId: bigint }> {
    // Validate amount is below threshold (500 cents = $5)
    if (amountCents > 500n) {
      throw new Error('Cash out only allowed for balances less than $5');
    }

    const giftCardLiabilityId = generateAccountId(
      cardId,
      AccountType.GIFT_CARD_LIABILITY,
      Ledger.USD
    );

    const transferId = idempotencyKey
      ? generateTransferIdFromReference(idempotencyKey)
      : generateTransferId();

    const transfer: Transfer = {
      id: transferId,
      debit_account_id: giftCardLiabilityId,
      credit_account_id: this.communityBankBridgeId,
      amount: amountCents,
      pending_id: 0n,
      user_data_128: 0n,
      user_data_64: 0n,
      user_data_32: 0,
      timeout: 0,
      ledger: Ledger.USD,
      code: TransferType.GIFT_CARD_CASHOUT,
      flags: 0,
      timestamp: 0n,
    };

    const errors = await this.client.createTransfers([transfer]);
    if (errors.length > 0 && errors[0].result !== 0 && errors[0].result !== 1) {
      throw new Error(
        `Failed to cash out gift card: ${handleTransferCreationError(errors[0].result)}`
      );
    }

    return { transferId };
  }

  // ==========================================================================
  // PAYOUT OPERATIONS
  // ==========================================================================

  /**
   * Process slow (free) payout via ACH
   */
  async processSlowPayout(
    vendorId: string,
    amountCents: bigint,
    idempotencyKey?: string
  ): Promise<{ transferId: bigint }> {
    const vendorEarningsId = generateAccountId(
      vendorId,
      AccountType.VENDOR_EARNINGS,
      Ledger.USD
    );

    const transferId = idempotencyKey
      ? generateTransferIdFromReference(idempotencyKey)
      : generateTransferId();

    const transfer = createSlowPayoutTransfer(
      transferId,
      vendorEarningsId,
      this.communityBankBridgeId,
      amountCents
    );

    const errors = await this.client.createTransfers([transfer]);
    if (errors.length > 0 && errors[0].result !== 0 && errors[0].result !== 1) {
      throw new Error(
        `Failed to process slow payout: ${handleTransferCreationError(errors[0].result)}`
      );
    }

    return { transferId };
  }

  /**
   * Process fast (fee-based) payout
   */
  async processFastPayout(
    vendorId: string,
    amountCents: bigint,
    feeCents: bigint,
    idempotencyKey?: string
  ): Promise<{ transferIds: bigint[] }> {
    const vendorEarningsId = generateAccountId(
      vendorId,
      AccountType.VENDOR_EARNINGS,
      Ledger.USD
    );

    const baseTransferId = idempotencyKey
      ? generateTransferIdFromReference(idempotencyKey)
      : generateTransferId();

    const transfers = createFastPayoutTransfers(
      baseTransferId,
      vendorEarningsId,
      this.communityBankBridgeId,
      this.feesPayoutFastId,
      amountCents,
      feeCents
    );

    const errors = await this.client.createTransfers(transfers);
    for (const error of errors) {
      if (error.result !== 0 && error.result !== 1) {
        throw new Error(
          `Failed to process fast payout: ${handleTransferCreationError(error.result)}`
        );
      }
    }

    return { transferIds: transfers.map(t => t.id) };
  }

  // ==========================================================================
  // TAX OPERATIONS
  // ==========================================================================

  /**
   * Pay GET from vendor tax reserve to HTO
   */
  async payGET(
    vendorId: string,
    amountCents: bigint,
    idempotencyKey?: string
  ): Promise<{ transferId: bigint }> {
    const vendorTaxReserveId = generateAccountId(
      vendorId,
      AccountType.VENDOR_TAX_RESERVE,
      Ledger.USD
    );

    const transferId = idempotencyKey
      ? generateTransferIdFromReference(idempotencyKey)
      : generateTransferId();

    const transfer = createTaxPaymentTransfer(
      transferId,
      vendorTaxReserveId,
      this.communityBankBridgeId,
      amountCents
    );

    const errors = await this.client.createTransfers([transfer]);
    if (errors.length > 0 && errors[0].result !== 0 && errors[0].result !== 1) {
      throw new Error(
        `Failed to pay GET: ${handleTransferCreationError(errors[0].result)}`
      );
    }

    return { transferId };
  }

  // ==========================================================================
  // KALA OPERATIONS
  // ==========================================================================

  /**
   * Award Kala for participation (separate KALA ledger)
   */
  async awardKala(
    participantId: string,
    kalaAmount: bigint,
    idempotencyKey?: string
  ): Promise<{ transferId: bigint }> {
    const participantKalaId = generateAccountId(
      participantId,
      AccountType.KALA_PARTICIPANT,
      Ledger.KALA
    );

    const transferId = idempotencyKey
      ? generateTransferIdFromReference(idempotencyKey)
      : generateTransferId();

    const transfer = createKalaAwardTransfer(
      transferId,
      this.kalaPoolId,
      participantKalaId,
      kalaAmount
    );

    const errors = await this.client.createTransfers([transfer]);
    if (errors.length > 0 && errors[0].result !== 0 && errors[0].result !== 1) {
      throw new Error(
        `Failed to award Kala: ${handleTransferCreationError(errors[0].result)}`
      );
    }

    return { transferId };
  }

  /**
   * Get participant Kala balance
   */
  async getKalaBalance(participantId: string): Promise<bigint> {
    const kalaId = generateAccountId(participantId, AccountType.KALA_PARTICIPANT, Ledger.KALA);
    const accounts = await this.client.lookupAccounts([kalaId]);

    if (accounts.length === 0) {
      return 0n;
    }

    return calculateBalance(accounts[0]);
  }

  // ==========================================================================
  // QUERY & REPORTING
  // ==========================================================================

  /**
   * Get account details by ID
   */
  async getAccount(accountId: bigint): Promise<Account | null> {
    const accounts = await this.client.lookupAccounts([accountId]);
    return accounts.length > 0 ? accounts[0] : null;
  }

  /**
   * Get transfer details by ID
   */
  async getTransfer(transferId: bigint): Promise<Transfer | null> {
    const transfers = await this.client.lookupTransfers([transferId]);
    return transfers.length > 0 ? transfers[0] : null;
  }

  /**
   * Get all balances for a vendor
   */
  async getVendorStatement(vendorId: string): Promise<{
    earnings: AccountBalance;
    taxReserve: AccountBalance;
    kala: AccountBalance;
  }> {
    const earningsId = generateAccountId(vendorId, AccountType.VENDOR_EARNINGS, Ledger.USD);
    const taxReserveId = generateAccountId(vendorId, AccountType.VENDOR_TAX_RESERVE, Ledger.USD);
    const kalaId = generateAccountId(vendorId, AccountType.KALA_PARTICIPANT, Ledger.KALA);

    const accounts = await this.client.lookupAccounts([earningsId, taxReserveId, kalaId]);

    return {
      earnings: {
        accountId: earningsId,
        debitsPosted: accounts[0].debits_posted,
        creditsPosted: accounts[0].credits_posted,
        debitsPending: accounts[0].debits_pending,
        creditsPending: accounts[0].credits_pending,
        balance: calculateBalance(accounts[0]),
        ledger: Ledger.USD,
        accountType: AccountType.VENDOR_EARNINGS,
      },
      taxReserve: {
        accountId: taxReserveId,
        debitsPosted: accounts[1].debits_posted,
        creditsPosted: accounts[1].credits_posted,
        debitsPending: accounts[1].debits_pending,
        creditsPending: accounts[1].credits_pending,
        balance: calculateBalance(accounts[1]),
        ledger: Ledger.USD,
        accountType: AccountType.VENDOR_TAX_RESERVE,
      },
      kala: {
        accountId: kalaId,
        debitsPosted: accounts[2].debits_posted,
        creditsPosted: accounts[2].credits_posted,
        debitsPending: accounts[2].debits_pending,
        creditsPending: accounts[2].credits_pending,
        balance: calculateBalance(accounts[2]),
        ledger: Ledger.KALA,
        accountType: AccountType.KALA_PARTICIPANT,
      },
    };
  }

  /**
   * Close the TigerBeetle client connection
   */
  async close(): Promise<void> {
    // TigerBeetle client cleanup if needed
  }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Convert USD dollars to cents (TigerBeetle uses integer amounts)
 */
export function dollarsToCents(dollars: number): bigint {
  return BigInt(Math.round(dollars * 100));
}

/**
 * Convert cents to dollars (for display)
 */
export function centsToDollars(cents: bigint): number {
  return Number(cents) / 100;
}

/**
 * Calculate GET amount from gross receipts
 */
export function calculateGET(grossReceiptsCents: bigint, getRate: number = 0.045): bigint {
  return BigInt(Math.floor(Number(grossReceiptsCents) * getRate));
}

/**
 * Calculate net earnings after GET
 */
export function calculateNetEarnings(grossReceiptsCents: bigint, getRate: number = 0.045): bigint {
  const getCents = calculateGET(grossReceiptsCents, getRate);
  return grossReceiptsCents - getCents;
}

// ============================================================================
// SINGLETON INSTANCE
// ============================================================================

let instance: OhanaLedgerService | null = null;

export function initializeOhanaLedger(config: OhanaLedgerConfig): OhanaLedgerService {
  if (instance) {
    throw new Error('Ohana Ledger already initialized');
  }
  instance = new OhanaLedgerService(config);
  return instance;
}

export function getOhanaLedger(): OhanaLedgerService {
  if (!instance) {
    throw new Error('Ohana Ledger not initialized. Call initializeOhanaLedger() first.');
  }
  return instance;
}
