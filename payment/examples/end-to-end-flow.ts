/**
 * End-to-End Example Flow
 *
 * Complete lifecycle demonstration:
 * 1. Donor buys $100 Ohana Gift Card
 * 2. Kupuna redeems card for meals from vendors
 * 3. GET accrues automatically
 * 4. Vendor requests slow payout (free)
 * 5. Vendor requests fast payout (with fee)
 * 6. Tax Orchestrator files and pays GET
 */

import { Pool } from 'pg';
import {
  OhanaLedgerService,
  initializeOhanaLedger,
  dollarsToCents,
  centsToDollars,
} from '../services/ohana-ledger';
import { GiftCardService } from '../services/gift-card-service';
import { PayoutOrchestrator, PayoutType } from '../services/payout-orchestrator';
import { TaxOrchestrator, FilingFrequency } from '../services/tax-orchestrator';
import { ACHProviderAdapter } from '../integrations/ach-provider-stub';
import { CardProcessorAdapter } from '../integrations/card-processor-stub';
import { HawaiiTaxOnlineAdapter } from '../integrations/hawaii-tax-online-stub';

// ============================================================================
// SETUP
// ============================================================================

async function setupServices() {
  // PostgreSQL connection
  const db = new Pool({
    connectionString: process.env.DATABASE_URL || 'postgresql://localhost/vessels_payment',
  });

  // Initialize Ohana Ledger (TigerBeetle)
  const ledger = initializeOhanaLedger({
    tigerbeetleClusterIds: [0],
    tigerbeetleReplicas: ['3000'],
    communityOrgId: 'community-org-uuid',
  });

  // Initialize external provider adapters
  const achProvider = new ACHProviderAdapter({
    apiKey: process.env.ACH_API_KEY || 'test',
    orgId: process.env.ACH_ORG_ID || 'test',
    baseUrl: 'https://api.moderntreasury.com',
  });

  const cardProcessor = new CardProcessorAdapter({
    apiKey: process.env.CARD_API_KEY || 'test',
    appToken: process.env.CARD_APP_TOKEN || 'test',
    programIdGet: 'get-reserve-program',
    programIdTax: 'tax-reserve-program',
  });

  const htoIntegration = new HawaiiTaxOnlineAdapter({
    mode: 'api',
    apiUrl: 'https://hitax.hawaii.gov/api',
    credentialVaultUrl: 'vault://credentials/hto',
  });

  // Initialize services
  const giftCardService = new GiftCardService(db);
  const payoutOrchestrator = new PayoutOrchestrator(
    db,
    achProvider as any,
    {} as any,
    cardProcessor as any
  );
  const taxOrchestrator = new TaxOrchestrator(db, htoIntegration as any);

  return {
    db,
    ledger,
    giftCardService,
    payoutOrchestrator,
    taxOrchestrator,
    achProvider,
    cardProcessor,
    htoIntegration,
  };
}

// ============================================================================
// SCENARIO: Complete Gift Card Lifecycle
// ============================================================================

async function runCompleteScenario() {
  console.log('\n='.repeat(70));
  console.log('VESSELS PAYMENT PLATFORM - END-TO-END FLOW');
  console.log('='.repeat(70));

  const services = await setupServices();
  const { ledger, giftCardService, payoutOrchestrator, taxOrchestrator } = services;

  // Initialize system accounts
  console.log('\n[1] Initializing system accounts...');
  await ledger.initializeSystemAccounts();
  console.log('✓ System accounts created');

  // ============================================================================
  // STEP 1: Create Vendors
  // ============================================================================

  console.log('\n[2] Onboarding vendors...');

  const vendor1Id = 'vendor-kupuna-kitchen-001';
  const vendor2Id = 'vendor-micro-farm-002';

  const vendor1Accounts = await ledger.createVendor(vendor1Id);
  const vendor2Accounts = await ledger.createVendor(vendor2Id);

  console.log(`✓ Vendor 1 created: Kupuna Kitchen`);
  console.log(`  - Earnings account: ${vendor1Accounts.earnings}`);
  console.log(`  - Tax reserve account: ${vendor1Accounts.taxReserve}`);
  console.log(`  - Kala account: ${vendor1Accounts.kala}`);

  console.log(`✓ Vendor 2 created: Micro Farm`);
  console.log(`  - Earnings account: ${vendor2Accounts.earnings}`);
  console.log(`  - Tax reserve account: ${vendor2Accounts.taxReserve}`);
  console.log(`  - Kala account: ${vendor2Accounts.kala}`);

  // ============================================================================
  // STEP 2: Donor Buys Gift Card ($100)
  // ============================================================================

  console.log('\n[3] Donor buys $100 Ohana Gift Card...');

  const donorId = 'donor-alice-001';
  const giftCard = await giftCardService.issueCard({
    initialBalanceUsd: 100.00,
    donorActorId: donorId,
  });

  console.log(`✓ Gift card issued`);
  console.log(`  - Card token: ${giftCard.cardToken}`);
  console.log(`  - Balance: $${giftCard.currentBalanceUsd}`);

  // Award Kala to donor
  await ledger.awardKala(donorId, 100n); // 100 kala for $100 donation
  console.log(`✓ Donor awarded 100 kala`);

  // ============================================================================
  // STEP 3: Kupuna Redeems Card at Vendors
  // ============================================================================

  console.log('\n[4] Kupuna redeems card at vendors...');

  // Redemption 1: $25 meal at Kupuna Kitchen
  const redemption1 = await giftCardService.redeemCard({
    cardToken: giftCard.cardToken,
    vendorId: vendor1Id,
    amountUsd: 25.00,
    locationDescription: 'Puna Farmers Market',
  });

  const getAmount1 = 25.00 * 0.045; // $1.13
  const netAmount1 = 25.00 - getAmount1; // $23.88

  console.log(`✓ Redemption 1: $25.00 at Kupuna Kitchen`);
  console.log(`  - Vendor earnings: $${netAmount1.toFixed(2)}`);
  console.log(`  - GET accrued: $${getAmount1.toFixed(2)}`);

  // Award Kala to vendor
  await ledger.awardKala(vendor1Id, 25n);
  console.log(`✓ Vendor 1 awarded 25 kala`);

  // Redemption 2: $30 produce at Micro Farm
  const redemption2 = await giftCardService.redeemCard({
    cardToken: giftCard.cardToken,
    vendorId: vendor2Id,
    amountUsd: 30.00,
  });

  const getAmount2 = 30.00 * 0.045; // $1.35
  const netAmount2 = 30.00 - getAmount2; // $28.65

  console.log(`✓ Redemption 2: $30.00 at Micro Farm`);
  console.log(`  - Vendor earnings: $${netAmount2.toFixed(2)}`);
  console.log(`  - GET accrued: $${getAmount2.toFixed(2)}`);

  await ledger.awardKala(vendor2Id, 30n);
  console.log(`✓ Vendor 2 awarded 30 kala`);

  // Check remaining card balance
  const remainingBalance = await giftCardService.getCardBalance(giftCard.cardToken);
  console.log(`\n✓ Gift card remaining balance: $${remainingBalance.toFixed(2)}`);

  // ============================================================================
  // STEP 4: Vendor 1 Requests Slow Payout (Free ACH)
  // ============================================================================

  console.log('\n[5] Vendor 1 requests slow (free) payout...');

  const slowPayout = await payoutOrchestrator.requestPayout({
    vendorId: vendor1Id,
    amountUsd: 20.00,
    payoutType: PayoutType.SLOW_FREE,
  });

  console.log(`✓ Slow payout requested`);
  console.log(`  - Amount: $${slowPayout.amountUsd}`);
  console.log(`  - Fee: $${slowPayout.feeUsd}`);
  console.log(`  - Net to vendor: $${slowPayout.netToVendorUsd}`);
  console.log(`  - Estimated delivery: 2-3 business days`);

  // Process slow payout batch (would normally be cron job)
  await payoutOrchestrator.processSlowPayoutBatch(10);
  console.log(`✓ Slow payout processed via ACH`);

  // ============================================================================
  // STEP 5: Vendor 2 Requests Fast Payout (With Fee)
  // ============================================================================

  console.log('\n[6] Vendor 2 requests fast (instant) payout...');

  // Get quote first
  const fastQuote = await payoutOrchestrator.getQuote(
    vendor2Id,
    28.65,
    PayoutType.FAST_FEE
  );

  console.log(`✓ Fast payout quote:`);
  console.log(`  - Amount: $${fastQuote.amountUsd}`);
  console.log(`  - Fee: $${fastQuote.feeUsd}`);
  console.log(`  - Net to vendor: $${fastQuote.netToVendorUsd}`);
  console.log(`  - Delivery: ${fastQuote.estimatedDelivery}`);

  const fastPayout = await payoutOrchestrator.requestPayout({
    vendorId: vendor2Id,
    amountUsd: 28.65,
    payoutType: PayoutType.FAST_FEE,
  });

  console.log(`✓ Fast payout completed instantly`);
  console.log(`  - Transaction ID: ${fastPayout.id}`);

  // ============================================================================
  // STEP 6: Check Vendor Balances
  // ============================================================================

  console.log('\n[7] Vendor balances after payouts...');

  const vendor1Balances = await ledger.getVendorBalances(vendor1Id);
  console.log(`\nVendor 1 (Kupuna Kitchen):`);
  console.log(`  - Earnings: $${centsToDollars(vendor1Balances.earnings).toFixed(2)}`);
  console.log(`  - Tax reserve: $${centsToDollars(vendor1Balances.taxReserve).toFixed(2)}`);
  console.log(`  - Kala: ${vendor1Balances.kala}`);

  const vendor2Balances = await ledger.getVendorBalances(vendor2Id);
  console.log(`\nVendor 2 (Micro Farm):`);
  console.log(`  - Earnings: $${centsToDollars(vendor2Balances.earnings).toFixed(2)}`);
  console.log(`  - Tax reserve: $${centsToDollars(vendor2Balances.taxReserve).toFixed(2)}`);
  console.log(`  - Kala: ${vendor2Balances.kala}`);

  // ============================================================================
  // STEP 7: Tax Filing (Quarterly GET)
  // ============================================================================

  console.log('\n[8] Scheduling quarterly GET filing for Vendor 1...');

  const periodStart = new Date('2025-10-01');
  const periodEnd = new Date('2025-12-31');
  const dueDate = new Date('2026-01-20');

  const taxFiling = await taxOrchestrator.scheduleFiling({
    vendorId: vendor1Id,
    periodStart,
    periodEnd,
    dueDate,
    filingFrequency: FilingFrequency.QUARTERLY,
  });

  console.log(`✓ Tax filing scheduled`);
  console.log(`  - Period: Q4 2025`);
  console.log(`  - Gross receipts: $${taxFiling.grossReceiptsUsd}`);
  console.log(`  - GET due: $${taxFiling.getDueUsd}`);
  console.log(`  - Due date: ${dueDate.toISOString().split('T')[0]}`);

  // File and pay GET
  console.log('\n[9] Filing and paying GET to Hawaii Tax Online...');
  const filedTax = await taxOrchestrator.fileAndPayGET(taxFiling.id);

  console.log(`✓ GET filed and paid`);
  console.log(`  - HTO confirmation: ${filedTax.htoConfirmationNumber}`);
  console.log(`  - Status: ${filedTax.status}`);

  // ============================================================================
  // SUMMARY
  // ============================================================================

  console.log('\n' + '='.repeat(70));
  console.log('SCENARIO COMPLETE');
  console.log('='.repeat(70));

  console.log('\nSummary:');
  console.log('- Donor purchased $100 gift card');
  console.log('- Kupuna made 2 purchases ($25 + $30)');
  console.log('- Vendors received earnings (net of GET)');
  console.log('- 1 slow payout processed (free ACH)');
  console.log('- 1 fast payout processed (instant, with fee)');
  console.log('- Quarterly GET filed and paid to Hawaii');
  console.log('- Kala awarded to all participants');

  console.log('\n✓ All operations completed successfully!');
  console.log('='.repeat(70) + '\n');

  // Cleanup
  await services.db.end();
}

// ============================================================================
// RUN SCENARIO
// ============================================================================

if (require.main === module) {
  runCompleteScenario()
    .then(() => {
      console.log('\nScenario execution completed.');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\nScenario execution failed:', error);
      process.exit(1);
    });
}

export { runCompleteScenario };
