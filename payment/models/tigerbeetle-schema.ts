/**
 * TigerBeetle Schema Definitions for Vessels Payment Platform
 *
 * TigerBeetle is a distributed financial accounting database with:
 * - Double-entry bookkeeping
 * - Strong consistency
 * - Idempotent transfers
 * - Full audit trail
 *
 * Docs: https://docs.tigerbeetle.com/
 */

import {
  Account,
  Transfer,
  AccountFlags,
  TransferFlags,
  CreateAccountError,
  CreateTransferError
} from 'tigerbeetle-node';

// ============================================================================
// LEDGER TYPES
// ============================================================================

/**
 * Separate ledgers for different value types
 * Critical: USD and Kala MUST NEVER be mixed in the same transfer
 */
export enum Ledger {
  USD = 1,   // Money ledger (all USD amounts)
  KALA = 2,  // Participation metric ledger (NOT money, never convertible)
}

// ============================================================================
// ACCOUNT TYPES
// ============================================================================

/**
 * Account type categorization using TigerBeetle's user_data_128 field
 * Bits 0-15: Account type code
 * Bits 16-31: Sub-type
 * Bits 32-127: Reserved for entity IDs
 */
export enum AccountType {
  // Vendor accounts (USD ledger)
  VENDOR_EARNINGS = 100,        // Spendable earnings after GET
  VENDOR_TAX_RESERVE = 101,     // Hawaii GET escrow (locked)

  // Community fund accounts (USD ledger)
  COMMUNITY_BANK_BRIDGE = 200,  // External bank balance mirror
  COMMUNITY_DONATIONS = 201,    // Received donations/grants
  COMMUNITY_SUBSIDIES = 202,    // Onboarding subsidies pool

  // Gift card accounts (USD ledger)
  GIFT_CARD_LIABILITY = 300,    // Per-card liability (what we owe holder)

  // Fee accounts (USD ledger)
  FEES_PAYOUT_FAST = 400,       // Fast payout fees collected
  FEES_PLATFORM = 401,          // General platform fees
  FEES_CARD_PROCESSING = 402,   // Card processing fees

  // Bridge accounts for external settlement (USD ledger)
  BRIDGE_MOJALOOP = 500,        // Mojaloop settlement account
  BRIDGE_ACH = 501,             // ACH settlement
  BRIDGE_RTP = 502,             // RTP/FedNow settlement
  BRIDGE_CARD = 503,            // Card processor settlement

  // Kala accounts (KALA ledger only)
  KALA_PARTICIPANT = 600,       // Per-participant Kala balance
  KALA_POOL = 601,              // Community Kala pool for awards
}

// ============================================================================
// TRANSFER TYPES
// ============================================================================

/**
 * Transfer codes identifying the business purpose
 */
export enum TransferType {
  // Gift card operations
  GIFT_CARD_LOAD = 1,           // Donor funds gift card
  GIFT_CARD_REDEMPTION = 2,     // Card used at vendor
  GIFT_CARD_CASHOUT = 3,        // HI law: <$5 cash redemption
  GIFT_CARD_REFUND = 4,         // Return/cancellation

  // Vendor operations
  SALE_REVENUE_SPLIT = 10,      // Split sale: earnings + GET
  PAYOUT_SLOW = 11,             // Free scheduled ACH payout
  PAYOUT_FAST = 12,             // Instant payout with fee
  PAYOUT_FAILED_REVERSAL = 13,  // Reverse failed payout

  // Tax operations
  TAX_ACCRUAL = 20,             // Accrue GET from sale
  TAX_PAYMENT = 21,             // Pay GET to HTO
  TAX_ADJUSTMENT = 22,          // Manual adjustment

  // External settlement
  EXTERNAL_CREDIT = 30,         // Money coming in (ACH, Mojaloop, etc.)
  EXTERNAL_DEBIT = 31,          // Money going out
  EXTERNAL_REVERSAL = 32,       // Settlement reversal

  // Platform operations
  FEE_COLLECTION = 40,          // Collect fee
  SUBSIDY_GRANT = 41,           // Onboarding subsidy to vendor

  // Kala operations (KALA ledger only)
  KALA_AWARD = 50,              // Award Kala for participation
  KALA_DECAY = 51,              // Time-based decay (optional)
  KALA_ADJUSTMENT = 52,         // Manual adjustment
}

// ============================================================================
// ACCOUNT CREATION HELPERS
// ============================================================================

export interface VendorAccountIds {
  earnings: bigint;      // VENDOR_EARNINGS account
  taxReserve: bigint;    // VENDOR_TAX_RESERVE account
  kala: bigint;          // KALA_PARTICIPANT account
}

export interface GiftCardAccountIds {
  liability: bigint;     // GIFT_CARD_LIABILITY account
}

/**
 * Generate TigerBeetle account ID from entity UUID and account type
 * Uses a deterministic hash to create unique 128-bit IDs
 */
export function generateAccountId(
  entityId: string,  // UUID of vendor/card/etc
  accountType: AccountType,
  ledger: Ledger
): bigint {
  // In production, use a proper hash function (e.g., xxHash)
  // This is a simplified example
  const entityHash = Buffer.from(entityId.replace(/-/g, ''), 'hex');
  const typeBuffer = Buffer.alloc(16);
  typeBuffer.writeBigUInt64BE(BigInt(accountType), 0);
  typeBuffer.writeBigUInt64BE(BigInt(ledger), 8);

  // Combine hashes
  const combined = Buffer.concat([entityHash, typeBuffer]);
  return BigInt('0x' + combined.slice(0, 16).toString('hex'));
}

/**
 * Create vendor accounts in TigerBeetle
 */
export function createVendorAccounts(
  vendorId: string,
  initialEarnings: bigint = 0n,
  initialTaxReserve: bigint = 0n
): { accounts: Account[], ids: VendorAccountIds } {
  const earningsId = generateAccountId(vendorId, AccountType.VENDOR_EARNINGS, Ledger.USD);
  const taxReserveId = generateAccountId(vendorId, AccountType.VENDOR_TAX_RESERVE, Ledger.USD);
  const kalaId = generateAccountId(vendorId, AccountType.KALA_PARTICIPANT, Ledger.KALA);

  const accounts: Account[] = [
    // Vendor earnings account (debit balance = money owed to vendor)
    {
      id: earningsId,
      debits_pending: 0n,
      debits_posted: initialEarnings,
      credits_pending: 0n,
      credits_posted: 0n,
      user_data_128: encodeAccountMetadata(AccountType.VENDOR_EARNINGS, vendorId),
      user_data_64: 0n,
      user_data_32: 0,
      reserved: 0,
      ledger: Ledger.USD,
      code: AccountType.VENDOR_EARNINGS,
      flags: 0, // Standard account
      timestamp: 0n, // TigerBeetle sets this
    },
    // Tax reserve account (debit balance = GET owed to state)
    {
      id: taxReserveId,
      debits_pending: 0n,
      debits_posted: initialTaxReserve,
      credits_pending: 0n,
      credits_posted: 0n,
      user_data_128: encodeAccountMetadata(AccountType.VENDOR_TAX_RESERVE, vendorId),
      user_data_64: 0n,
      user_data_32: 0,
      reserved: 0,
      ledger: Ledger.USD,
      code: AccountType.VENDOR_TAX_RESERVE,
      flags: 0,
      timestamp: 0n,
    },
    // Kala account (separate ledger)
    {
      id: kalaId,
      debits_pending: 0n,
      debits_posted: 0n,
      credits_pending: 0n,
      credits_posted: 0n,
      user_data_128: encodeAccountMetadata(AccountType.KALA_PARTICIPANT, vendorId),
      user_data_64: 0n,
      user_data_32: 0,
      reserved: 0,
      ledger: Ledger.KALA,
      code: AccountType.KALA_PARTICIPANT,
      flags: 0,
      timestamp: 0n,
    }
  ];

  return {
    accounts,
    ids: {
      earnings: earningsId,
      taxReserve: taxReserveId,
      kala: kalaId,
    }
  };
}

/**
 * Create gift card liability account
 */
export function createGiftCardAccount(
  cardId: string,
  initialBalance: bigint = 0n
): { account: Account, ids: GiftCardAccountIds } {
  const liabilityId = generateAccountId(cardId, AccountType.GIFT_CARD_LIABILITY, Ledger.USD);

  const account: Account = {
    id: liabilityId,
    debits_pending: 0n,
    debits_posted: 0n,
    credits_pending: 0n,
    credits_posted: initialBalance, // Credit balance = what we owe to cardholder
    user_data_128: encodeAccountMetadata(AccountType.GIFT_CARD_LIABILITY, cardId),
    user_data_64: 0n,
    user_data_32: 0,
    reserved: 0,
    ledger: Ledger.USD,
    code: AccountType.GIFT_CARD_LIABILITY,
    flags: 0,
    timestamp: 0n,
  };

  return {
    account,
    ids: { liability: liabilityId }
  };
}

/**
 * Encode account metadata into user_data_128
 * Format: [account_type: 16 bits][reserved: 16 bits][entity_uuid: 96 bits]
 */
function encodeAccountMetadata(accountType: AccountType, entityId: string): bigint {
  const uuidBuffer = Buffer.from(entityId.replace(/-/g, ''), 'hex').slice(0, 12);
  const metadataBuffer = Buffer.alloc(16);

  // Bits 0-15: account type
  metadataBuffer.writeUInt16BE(accountType, 0);
  // Bits 16-31: reserved (0)
  metadataBuffer.writeUInt16BE(0, 2);
  // Bits 32-127: entity UUID (first 96 bits)
  uuidBuffer.copy(metadataBuffer, 4);

  return BigInt('0x' + metadataBuffer.toString('hex'));
}

// ============================================================================
// TRANSFER CREATION HELPERS
// ============================================================================

/**
 * Create a gift card load transfer
 * Donor pays → gift card liability increases
 */
export function createGiftCardLoadTransfer(
  transferId: bigint,
  communityBankBridgeId: bigint,
  giftCardLiabilityId: bigint,
  amountCents: bigint,
  timeout: number = 0
): Transfer {
  return {
    id: transferId,
    debit_account_id: communityBankBridgeId,
    credit_account_id: giftCardLiabilityId,
    amount: amountCents,
    pending_id: 0n,
    user_data_128: 0n,
    user_data_64: 0n,
    user_data_32: 0,
    timeout,
    ledger: Ledger.USD,
    code: TransferType.GIFT_CARD_LOAD,
    flags: 0, // Posted immediately
    timestamp: 0n,
  };
}

/**
 * Create a gift card redemption transfer (multi-leg)
 * Card liability decreases → vendor earnings + tax reserve increases
 *
 * Returns array of transfers for atomic execution:
 * 1. Debit gift card
 * 2. Credit vendor earnings (net)
 * 3. Credit vendor tax reserve (GET portion)
 */
export function createGiftCardRedemptionTransfers(
  baseTransferId: bigint,
  giftCardLiabilityId: bigint,
  vendorEarningsId: bigint,
  vendorTaxReserveId: bigint,
  totalAmountCents: bigint,
  getRate: number // e.g., 0.045 for 4.5%
): Transfer[] {
  const getCents = BigInt(Math.floor(Number(totalAmountCents) * getRate));
  const netCents = totalAmountCents - getCents;

  return [
    // Transfer 1: Debit gift card liability (reduce what we owe)
    {
      id: baseTransferId,
      debit_account_id: giftCardLiabilityId,
      credit_account_id: vendorEarningsId,
      amount: netCents,
      pending_id: 0n,
      user_data_128: 0n,
      user_data_64: 0n,
      user_data_32: 0,
      timeout: 0,
      ledger: Ledger.USD,
      code: TransferType.GIFT_CARD_REDEMPTION,
      flags: 0,
      timestamp: 0n,
    },
    // Transfer 2: Debit gift card for GET portion → credit tax reserve
    {
      id: baseTransferId + 1n,
      debit_account_id: giftCardLiabilityId,
      credit_account_id: vendorTaxReserveId,
      amount: getCents,
      pending_id: 0n,
      user_data_128: 0n,
      user_data_64: 0n,
      user_data_32: 0,
      timeout: 0,
      ledger: Ledger.USD,
      code: TransferType.TAX_ACCRUAL,
      flags: 0,
      timestamp: 0n,
    }
  ];
}

/**
 * Create a slow payout transfer (free ACH)
 * Vendor earnings → community bank bridge (for ACH out)
 */
export function createSlowPayoutTransfer(
  transferId: bigint,
  vendorEarningsId: bigint,
  communityBankBridgeId: bigint,
  amountCents: bigint
): Transfer {
  return {
    id: transferId,
    debit_account_id: vendorEarningsId,
    credit_account_id: communityBankBridgeId,
    amount: amountCents,
    pending_id: 0n,
    user_data_128: 0n,
    user_data_64: 0n,
    user_data_32: 0,
    timeout: 0,
    ledger: Ledger.USD,
    code: TransferType.PAYOUT_SLOW,
    flags: 0,
    timestamp: 0n,
  };
}

/**
 * Create a fast payout transfer with fee (instant)
 * Returns array of transfers:
 * 1. Debit vendor earnings (full amount)
 * 2. Credit community bank bridge (net to vendor)
 * 3. Credit fees account (vendor fee)
 */
export function createFastPayoutTransfers(
  baseTransferId: bigint,
  vendorEarningsId: bigint,
  communityBankBridgeId: bigint,
  feesAccountId: bigint,
  amountCents: bigint,
  feeCents: bigint
): Transfer[] {
  const netCents = amountCents - feeCents;

  return [
    // Transfer 1: Debit vendor earnings for net amount
    {
      id: baseTransferId,
      debit_account_id: vendorEarningsId,
      credit_account_id: communityBankBridgeId,
      amount: netCents,
      pending_id: 0n,
      user_data_128: 0n,
      user_data_64: 0n,
      user_data_32: 0,
      timeout: 0,
      ledger: Ledger.USD,
      code: TransferType.PAYOUT_FAST,
      flags: 0,
      timestamp: 0n,
    },
    // Transfer 2: Debit vendor earnings for fee → credit fees account
    {
      id: baseTransferId + 1n,
      debit_account_id: vendorEarningsId,
      credit_account_id: feesAccountId,
      amount: feeCents,
      pending_id: 0n,
      user_data_128: 0n,
      user_data_64: 0n,
      user_data_32: 0,
      timeout: 0,
      ledger: Ledger.USD,
      code: TransferType.FEE_COLLECTION,
      flags: 0,
      timestamp: 0n,
    }
  ];
}

/**
 * Create a tax payment transfer
 * Vendor tax reserve → community bank bridge (for payment to HTO)
 */
export function createTaxPaymentTransfer(
  transferId: bigint,
  vendorTaxReserveId: bigint,
  communityBankBridgeId: bigint,
  amountCents: bigint
): Transfer {
  return {
    id: transferId,
    debit_account_id: vendorTaxReserveId,
    credit_account_id: communityBankBridgeId,
    amount: amountCents,
    pending_id: 0n,
    user_data_128: 0n,
    user_data_64: 0n,
    user_data_32: 0,
    timeout: 0,
    ledger: Ledger.USD,
    code: TransferType.TAX_PAYMENT,
    flags: 0,
    timestamp: 0n,
  };
}

/**
 * Create a Kala award transfer (separate KALA ledger)
 * Kala pool → participant Kala account
 */
export function createKalaAwardTransfer(
  transferId: bigint,
  kalaPoolId: bigint,
  participantKalaId: bigint,
  kalaAmount: bigint
): Transfer {
  return {
    id: transferId,
    debit_account_id: kalaPoolId,
    credit_account_id: participantKalaId,
    amount: kalaAmount,
    pending_id: 0n,
    user_data_128: 0n,
    user_data_64: 0n,
    user_data_32: 0,
    timeout: 0,
    ledger: Ledger.KALA, // Separate ledger!
    code: TransferType.KALA_AWARD,
    flags: 0,
    timestamp: 0n,
  };
}

// ============================================================================
// QUERY HELPERS
// ============================================================================

export interface AccountBalance {
  accountId: bigint;
  debitsPosted: bigint;
  creditsPosted: bigint;
  debitsPending: bigint;
  creditsPending: bigint;
  balance: bigint; // net = debits - credits (or credits - debits for liabilities)
  ledger: Ledger;
  accountType: AccountType;
}

/**
 * Calculate net balance for an account
 * For asset/expense accounts: balance = debits - credits
 * For liability/revenue accounts: balance = credits - debits
 */
export function calculateBalance(account: Account, isLiability: boolean = false): bigint {
  const netDebits = account.debits_posted + account.debits_pending;
  const netCredits = account.credits_posted + account.credits_pending;

  if (isLiability) {
    return netCredits - netDebits; // Credit balance for liabilities
  } else {
    return netDebits - netCredits; // Debit balance for assets
  }
}

/**
 * Check if account type is a liability
 */
export function isLiabilityAccount(accountType: AccountType): boolean {
  return [
    AccountType.GIFT_CARD_LIABILITY,
    AccountType.COMMUNITY_DONATIONS,
  ].includes(accountType);
}

// ============================================================================
// TRANSFER ID GENERATION
// ============================================================================

/**
 * Generate unique transfer ID
 * Use UUIDv7 or similar for time-ordered uniqueness
 */
export function generateTransferId(): bigint {
  // In production, use UUIDv7 or snowflake ID
  // This is simplified
  const timestamp = BigInt(Date.now());
  const random = BigInt(Math.floor(Math.random() * 0xFFFFFFFF));
  return (timestamp << 32n) | random;
}

/**
 * Generate deterministic transfer ID from external reference
 * Useful for idempotency with external systems
 */
export function generateTransferIdFromReference(reference: string): bigint {
  // Hash the reference string to get deterministic ID
  const hash = Buffer.from(reference).reduce((acc, byte) => acc + byte, 0);
  return BigInt(hash) << 32n | BigInt(Date.now() & 0xFFFFFFFF);
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

export function handleAccountCreationError(error: CreateAccountError): string {
  switch (error) {
    case CreateAccountError.exists:
      return 'Account already exists';
    case CreateAccountError.exists_with_different_flags:
      return 'Account exists with different flags';
    case CreateAccountError.exists_with_different_user_data_128:
      return 'Account exists with different metadata';
    case CreateAccountError.exists_with_different_user_data_64:
      return 'Account exists with different user data';
    case CreateAccountError.exists_with_different_user_data_32:
      return 'Account exists with different user data';
    case CreateAccountError.exists_with_different_ledger:
      return 'Account exists on different ledger';
    case CreateAccountError.exists_with_different_code:
      return 'Account exists with different code';
    default:
      return `Account creation error: ${error}`;
  }
}

export function handleTransferCreationError(error: CreateTransferError): string {
  switch (error) {
    case CreateTransferError.exists:
      return 'Transfer already exists (duplicate ID)';
    case CreateTransferError.exists_with_different_flags:
      return 'Transfer exists with different flags';
    case CreateTransferError.exists_with_different_debit_account_id:
      return 'Transfer exists with different debit account';
    case CreateTransferError.exists_with_different_credit_account_id:
      return 'Transfer exists with different credit account';
    case CreateTransferError.exists_with_different_amount:
      return 'Transfer exists with different amount';
    case CreateTransferError.exists_with_different_pending_id:
      return 'Transfer exists with different pending ID';
    case CreateTransferError.exists_with_different_user_data_128:
      return 'Transfer exists with different metadata';
    case CreateTransferError.exists_with_different_user_data_64:
      return 'Transfer exists with different user data';
    case CreateTransferError.exists_with_different_user_data_32:
      return 'Transfer exists with different user data';
    case CreateTransferError.exists_with_different_timeout:
      return 'Transfer exists with different timeout';
    case CreateTransferError.exists_with_different_code:
      return 'Transfer exists with different code';
    case CreateTransferError.exceeds_credits:
      return 'Insufficient balance: would exceed available credits';
    case CreateTransferError.exceeds_debits:
      return 'Insufficient balance: would exceed available debits';
    case CreateTransferError.debit_account_not_found:
      return 'Debit account not found';
    case CreateTransferError.credit_account_not_found:
      return 'Credit account not found';
    case CreateTransferError.accounts_must_be_different:
      return 'Debit and credit accounts must be different';
    case CreateTransferError.ledger_must_match:
      return 'Transfer ledger must match account ledgers';
    default:
      return `Transfer creation error: ${error}`;
  }
}

// ============================================================================
// TYPESCRIPT TYPE GUARDS
// ============================================================================

export function isUSDLedger(ledger: Ledger): ledger is Ledger.USD {
  return ledger === Ledger.USD;
}

export function isKalaLedger(ledger: Ledger): ledger is Ledger.KALA {
  return ledger === Ledger.KALA;
}

/**
 * Type guard to ensure transfers don't mix ledgers
 */
export function validateTransferLedger(
  transfer: Transfer,
  debitAccount: Account,
  creditAccount: Account
): boolean {
  return (
    transfer.ledger === debitAccount.ledger &&
    transfer.ledger === creditAccount.ledger
  );
}
