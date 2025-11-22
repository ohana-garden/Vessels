# External Integration Adapters

This directory contains adapter implementations for external services used by the Vessels payment platform.

## Adapters

### 1. ACH Provider (Plaid / Modern Treasury)

**File:** `ach-provider.ts`

Handles standard ACH transfers for slow payouts.

**Interface:**
```typescript
interface ACHProvider {
  initiateCredit(params: {
    vendorId: string;
    amountUsd: number;
    idempotencyKey: string;
  }): Promise<{ transactionId: string; costUsd: number }>;
}
```

### 2. RTP / FedNow Provider

**File:** `rtp-provider.ts`

Handles real-time payment transfers for fast payouts.

**Interface:**
```typescript
interface RTPProvider {
  sendPayment(params: {
    vendorId: string;
    amountUsd: number;
    idempotencyKey: string;
  }): Promise<{ transactionId: string; costUsd: number }>;
}
```

### 3. Card Processor (Marqeta / Stripe Issuing)

**File:** `card-processor.ts`

Issues GET Reserve Cards and Tax Reserve Cards, handles push-to-debit payouts.

**Interface:**
```typescript
interface CardProcessor {
  // Card issuance
  issueCard(params: {
    userId: string;
    cardType: 'get_reserve' | 'tax_reserve';
  }): Promise<{ programId: string; lastFour: string }>;

  // Push-to-debit payout
  pushToDebit(params: {
    vendorId: string;
    amountUsd: number;
    idempotencyKey: string;
  }): Promise<{ transactionId: string; costUsd: number }>;
}
```

### 4. Hawaii Tax Online (HTO) Integration

**File:** `hawaii-tax-online.ts`

Automates GET filing and payment via HTO API or headless browser.

**Interface:**
```typescript
interface HawaiiTaxOnlineIntegration {
  fileGET(params: {
    vendorId: string;
    periodStart: Date;
    periodEnd: Date;
    grossReceipts: number;
    getDue: number;
  }): Promise<{ confirmationNumber: string }>;

  payGET(params: {
    vendorId: string;
    amountUsd: number;
    confirmationNumber: string;
  }): Promise<{ transactionId: string }>;
}
```

### 5. Mojaloop SDK

**File:** `mojaloop-sdk.ts`

Official Mojaloop SDK wrapper for FSPIOP protocol.

**Interface:**
```typescript
interface MojaloopSDK {
  requestQuote(params: QuoteParams): Promise<QuoteResponse>;
  prepareTransfer(params: TransferParams): Promise<TransferResponse>;
  commitTransfer(params: CommitParams): Promise<void>;
}
```

## Configuration

All adapters are configured via environment variables:

```env
# ACH Provider (Modern Treasury)
ACH_PROVIDER=modern_treasury
MODERN_TREASURY_API_KEY=mt_live_xxx
MODERN_TREASURY_ORG_ID=org_xxx

# Card Processor (Marqeta)
CARD_PROCESSOR=marqeta
MARQETA_API_KEY=xxx
MARQETA_APP_TOKEN=xxx
MARQETA_PROGRAM_ID_GET=xxx
MARQETA_PROGRAM_ID_TAX=xxx

# Hawaii Tax Online
HTO_INTEGRATION_MODE=api  # or 'headless'
HTO_API_URL=https://hitax.hawaii.gov/api
HTO_CREDENTIAL_VAULT_URL=vault://credentials/hto

# Mojaloop
MOJALOOP_SWITCH_URL=https://mojaloop.hawaii.gov
MOJALOOP_PARTICIPANT_ID=vessels-dfsp
MOJALOOP_API_KEY=xxx
MOJALOOP_CALLBACK_URL=https://api.vessels.ohana/webhooks/mojaloop
```

## Error Handling

All adapters follow a consistent error handling pattern:

```typescript
class ExternalServiceError extends Error {
  constructor(
    public provider: string,
    public code: string,
    public message: string,
    public retryable: boolean = false
  ) {
    super(message);
  }
}
```

## Retry Logic

Adapters implement exponential backoff for retryable errors:

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelayMs: number = 1000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries || !(error as ExternalServiceError).retryable) {
        throw error;
      }
      await sleep(baseDelayMs * Math.pow(2, attempt));
    }
  }
  throw new Error('Max retries exceeded');
}
```

## Testing

Mock implementations provided in `__mocks__/` for testing:

```typescript
import { MockACHProvider } from './__mocks__/ach-provider';
import { MockCardProcessor } from './__mocks__/card-processor';
import { MockHTOIntegration } from './__mocks__/hawaii-tax-online';
```

## Security

### Credential Management

- All API keys stored in secure vault (HashiCorp Vault or AWS Secrets Manager)
- Credentials rotated every 90 days
- Access logged and audited

### Data Encryption

- All API requests use TLS 1.3
- Sensitive data encrypted at rest
- PCI DSS compliance for card data

### Rate Limiting

- Respect provider rate limits
- Implement circuit breaker pattern
- Graceful degradation on service failures
