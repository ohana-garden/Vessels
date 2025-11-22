/**
 * Card Processor Adapter (Stub Implementation)
 *
 * Production implementation would use Marqeta, Stripe Issuing, or similar.
 */

export interface CardProcessorConfig {
  apiKey: string;
  appToken: string;
  programIdGet: string;  // GET Reserve Card program
  programIdTax: string;  // Tax Reserve Card program
}

export class CardProcessorAdapter {
  constructor(private config: CardProcessorConfig) {}

  /**
   * Issue GET Reserve Card or Tax Reserve Card
   */
  async issueCard(params: {
    userId: string;
    cardType: 'get_reserve' | 'tax_reserve';
    email: string;
  }): Promise<{ programId: string; lastFour: string; cardToken: string }> {
    // TODO: Implement actual card issuance via Marqeta/Stripe
    console.log(`[CARD] Issuing ${params.cardType} card for user ${params.userId}`);

    return {
      programId: `card_${Date.now()}`,
      lastFour: '1234',
      cardToken: `tok_${Math.random().toString(36).substr(2, 16)}`,
    };
  }

  /**
   * Push-to-debit payout (instant)
   */
  async pushToDebit(params: {
    vendorId: string;
    amountUsd: number;
    idempotencyKey: string;
  }): Promise<{ transactionId: string; costUsd: number }> {
    // TODO: Implement actual push-to-debit via card network
    console.log(`[CARD] Push-to-debit: $${params.amountUsd} to vendor ${params.vendorId}`);

    return {
      transactionId: `ptd_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      costUsd: Math.max(params.amountUsd * 0.015, 0.25), // 1.5% or $0.25
    };
  }

  /**
   * Get card balance
   */
  async getCardBalance(cardToken: string): Promise<number> {
    // TODO: Implement balance query
    return 0;
  }
}
