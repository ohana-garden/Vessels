/**
 * Hawaii Tax Online (HTO) Integration Adapter (Stub)
 *
 * Production implementation would use:
 * - Official HTO API (if available), or
 * - Headless browser automation (Playwright/Puppeteer)
 *
 * SECURITY: Vendor credentials stored in encrypted vault, not in code.
 */

export interface HTOConfig {
  mode: 'api' | 'headless';
  apiUrl?: string;
  credentialVaultUrl: string;
}

export class HawaiiTaxOnlineAdapter {
  constructor(private config: HTOConfig) {}

  /**
   * File GET return with HTO
   */
  async fileGET(params: {
    vendorId: string;
    periodStart: Date;
    periodEnd: Date;
    grossReceipts: number;
    getDue: number;
  }): Promise<{ confirmationNumber: string }> {
    // TODO: Implement actual HTO filing
    // If API mode: POST to HTO API
    // If headless mode: Use Playwright to fill form

    console.log(`[HTO] Filing GET for vendor ${params.vendorId}`);
    console.log(`  Period: ${params.periodStart} to ${params.periodEnd}`);
    console.log(`  Gross receipts: $${params.grossReceipts}`);
    console.log(`  GET due: $${params.getDue}`);

    // Simulate filing
    const confirmationNumber = `HTO-${Date.now()}-${Math.random().toString(36).substr(2, 6).toUpperCase()}`;

    return { confirmationNumber };
  }

  /**
   * Pay GET via ACH debit from tax reserve account
   */
  async payGET(params: {
    vendorId: string;
    amountUsd: number;
    confirmationNumber: string;
  }): Promise<{ transactionId: string }> {
    // TODO: Implement payment submission to HTO
    console.log(`[HTO] Paying GET: $${params.amountUsd} for confirmation ${params.confirmationNumber}`);

    return {
      transactionId: `HTO-PAY-${Date.now()}`,
    };
  }

  /**
   * Get filing status from HTO
   */
  async getFilingStatus(confirmationNumber: string): Promise<{
    status: 'submitted' | 'processing' | 'accepted' | 'rejected';
    message?: string;
  }> {
    // TODO: Implement status check
    return {
      status: 'accepted',
      message: 'Filing accepted by HTO',
    };
  }
}
