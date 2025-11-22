# Vessels Payment Platform Architecture

## Overview

The Vessels neighborhood payment platform is a two-layer money system designed for ethical, transparent, and compliant community commerce in Hawaiʻi.

**Platform Names:**
- Overall platform: **Vessels**
- Vendor spending instrument: **GET Reserve Card**
- Vendor tax bucket instrument: **Tax Reserve Account / Card**
- Gift instrument: **Ohana Gift Card**
- Internal ledger + agents layer: **Ohana Ledger**

## Architecture Principles

### 1. Two-Layer Money Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: External Money Rails                 │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ Bank Accounts│  │   Mojaloop   │  │ ACH/RTP/FedNow/Card │   │
│  │ (Community   │  │   DFSPs      │  │   Processors        │   │
│  │  Org + Users)│  │              │  │                     │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│            LAYER 2: Internal High-Resolution Ledger              │
│                    (TigerBeetle Core)                            │
│                                                                  │
│  • USD obligations (double-entry)                                │
│  • Kala participation metrics (separate ledger, NOT money)       │
│  • Tax accruals (Hawaii GET)                                     │
│  • Gift card liabilities                                         │
│  • Idempotent, atomic transfers                                  │
│  • Full audit trail                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Regulatory Perimeter

**NOT a Money Transmitter:**
- No pooled omnibus customer funds
- All real funds belong to:
  - Individual humans (households, sole-props), OR
  - Single community fund organization (nonprofit/coop with EIN)
- KYC happens at banks/DFSPs, not inside Vessels
- Participants are primarily sole proprietors using SSN (not EIN)

**Single Community Organization:**
- One nonprofit/coop with EIN serves as:
  - Receiver of donations, grants, platform margins
  - Funder of onboarding grants and subsidies
  - Settlement entity for gift card vendor payouts

## System Architecture

### Service Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│                  (GraphQL + REST endpoints)                      │
└─────────────┬───────────────────────────────────────────────────┘
              │
    ┌─────────┴──────────┬────────────┬─────────────┬────────────┐
    │                    │            │             │            │
    ▼                    ▼            ▼             ▼            ▼
┌─────────┐      ┌─────────────┐  ┌──────┐  ┌──────────┐  ┌──────────┐
│ Gift    │      │   Payout    │  │ Tax  │  │ Vendor   │  │ Agent    │
│ Card    │      │Orchestrator │  │Orch. │  │Onboarding│  │  Layer   │
│ Service │      │             │  │      │  │          │  │          │
└────┬────┘      └──────┬──────┘  └───┬──┘  └────┬─────┘  └────┬─────┘
     │                  │             │          │             │
     └──────────────────┴─────────────┴──────────┴─────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Ohana Ledger API    │
                    │  (TigerBeetle Client) │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   TigerBeetle Cluster │
                    │  (Core Ledger Engine) │
                    │                       │
                    │  • Accounts           │
                    │  • Transfers          │
                    │  • Balances           │
                    │  • Audit log          │
                    └───────────────────────┘
```

### External Integrations

```
┌─────────────────────────────────────────────────────────────────┐
│                    Vessels Payment Services                      │
└─────┬───────────────┬──────────────┬─────────────┬──────────────┘
      │               │              │             │
      ▼               ▼              ▼             ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐
│ Mojaloop │   │   Card   │   │ ACH/RTP  │   │   Hawaiʻi    │
│   Hub    │   │Processor │   │ Provider │   │ Tax Online   │
│          │   │          │   │          │   │    (HTO)     │
│ (FSPIOP) │   │ (GET +   │   │(Plaid/   │   │              │
│          │   │  Tax     │   │ Modern   │   │ (Tax filing  │
│          │   │  Cards)  │   │ Treasury)│   │  & payment)  │
└──────────┘   └──────────┘   └──────────┘   └──────────────┘
```

## Core Services

### 1. Ohana Ledger Service (TigerBeetle)

**Technology:** TigerBeetle - distributed financial accounting database

**Account Structure:**

```typescript
// TigerBeetle account types (using ledger field for categorization)
enum Ledger {
  USD = 1,              // Money ledger
  KALA = 2,             // Participation metric ledger (NOT money)
}

enum AccountType {
  // Vendor accounts
  VENDOR_EARNINGS = 100,       // Spendable earnings
  VENDOR_TAX_RESERVE = 101,    // Hawaii GET escrow

  // Community fund accounts
  COMMUNITY_BANK_BRIDGE = 200, // External bank balance
  COMMUNITY_DONATIONS = 201,   // Received donations

  // Gift card accounts
  GIFT_CARD_LIABILITY = 300,   // Per-card liability

  // Fee accounts
  FEES_PAYOUT_FAST = 400,      // Fast payout fees collected
  FEES_PLATFORM = 401,         // Platform fees

  // Bridge accounts (external settlement)
  BRIDGE_MOJALOOP = 500,       // Mojaloop settlement
  BRIDGE_ACH = 501,            // ACH settlement
  BRIDGE_CARD = 502,           // Card settlement

  // Kala accounts (separate ledger)
  KALA_PARTICIPANT = 600,      // Per-participant Kala balance
}
```

**Transfer Types:**

```typescript
enum TransferType {
  // Gift card operations
  GIFT_CARD_LOAD = 1,          // Donor loads gift card
  GIFT_CARD_REDEMPTION = 2,    // Card used at vendor
  GIFT_CARD_CASHOUT = 3,       // HI law: <$5 cash redemption

  // Vendor operations
  SALE_REVENUE_SPLIT = 10,     // Split sale into earnings + GET
  PAYOUT_SLOW = 11,            // Free ACH payout
  PAYOUT_FAST = 12,            // Fee-based instant payout

  // Tax operations
  TAX_PAYMENT = 20,            // GET payment to HTO

  // External settlement
  EXTERNAL_CREDIT = 30,        // Money coming in
  EXTERNAL_DEBIT = 31,         // Money going out

  // Kala operations (separate ledger)
  KALA_AWARD = 40,             // Award Kala for participation
  KALA_DECAY = 41,             // Optional: time-based decay
}
```

**Key Features:**
- **Idempotent transfers** using TigerBeetle's unique transfer IDs
- **Atomic multi-leg transfers** for complex operations (e.g., sale with GET split)
- **Strong consistency** across all accounts
- **Audit trail** with full journal history
- **Separate ledgers** for USD vs Kala (never mixed)
- **Account balance queries** with point-in-time snapshots

### 2. Gift Card Service

**Closed-loop prepaid system** (FinCEN compliant):

- Cards usable only within Ohana merchant network
- Per-card daily load limit ≤ $2,000 USD
- No consumer ATM access except HI law: <$5 cash redemption
- No P2P transfers between consumers

**Operations:**
1. **Issue card**: Donor pays → credit gift_card_liability
2. **Redeem card**: Purchase → debit card, credit vendor (earnings + tax)
3. **Cashout**: Balance <$5 → debit card, credit community bank bridge

### 3. Payout Orchestrator Service

**Two payout modes:**

**Slow (free) payout:**
- Scheduled batches (e.g., weekly)
- Standard ACH from community org to vendor GET card
- No fee to vendor (absorbed into platform economics)

**Fast (fee) payout:**
- On-demand instant payout
- Push-to-debit (OCT) or RTP/FedNow
- Vendor pays fee (e.g., max(1%, $0.50))
- Platform keeps margin after covering rail costs

**Rail Selection:**
```typescript
interface PayoutRail {
  type: 'ACH' | 'RTP' | 'FedNow' | 'PushToDebit';
  speed: 'instant' | 'same_day' | 'next_day' | 'standard';
  cost: number;  // USD cost to platform
  vendorFee: number;  // USD fee charged to vendor
}
```

### 4. Tax Orchestrator Service

**Hawaii GET (General Excise Tax) automation:**

- Default rate: 4.5% (4% state + 0.5% county)
- Per-sale: split gross into (net earnings + GET reserve)
- Track vendor filing frequency (monthly/quarterly/annual)
- Generate tax period summaries
- Integrate with Hawaiʻi Tax Online (HTO):
  - Official API if available
  - Headless browser automation otherwise
- Initiate ACH debit from vendor Tax Reserve account to HTO

**Security:**
- Vendor credentials stored in encrypted vault
- Explicit consent flow for tax automation
- Manual override available (with warnings)

### 5. Mojaloop Connector Service

**Integration with Mojaloop instant payment hub:**

- Implements FSPIOP API (Financial Services Interoperability Protocol)
- Represents community fund org as DFSP participant
- Handles:
  - Participant registration
  - Quote requests
  - Transfer execution
  - Settlement callbacks

**Mapping to Ohana Ledger:**
- Incoming Mojaloop credit → credit community_bank_bridge or vendor account
- Outgoing Mojaloop debit → debit community_bank_bridge

**Fallback:**
- If Mojaloop unavailable in region → transparent fallback to ACH/card rails
- All Mojaloop logic encapsulated in connector service

### 6. Vendor Onboarding Service

**Minimal KYC (delegated to banks):**

- Collect:
  - Name, business description
  - GET Reserve Card program account ID
  - Tax Reserve account ID
  - SSN/EIN (prefer SSN for sole props)
  - Tax filing frequency
- Link vendor accounts in Ohana Ledger
- Create initial vendor accounts in TigerBeetle

**NOT stored:**
- Full KYC documents
- Bank account credentials (only tokens/IDs)

## Data Flow Examples

### Example 1: Gift Card Purchase and Redemption

```
1. DONOR LOADS GIFT CARD ($100)
   External: Donor pays $100 to community org bank account

   TigerBeetle Transfer:
     Debit:  community_bank_bridge         $100
     Credit: gift_card_liability:CARD_123  $100
     Type:   GIFT_CARD_LOAD

2. KUPUNA REDEEMS CARD AT VENDOR ($10 meal)
   GET rate: 4.5%
   Vendor net: $9.55
   GET: $0.45

   TigerBeetle Transfer (atomic multi-leg):
     Debit:  gift_card_liability:CARD_123    $10.00
     Credit: vendor:earnings:V1              $9.55
     Credit: vendor:tax_reserve:V1           $0.45
     Type:   GIFT_CARD_REDEMPTION

   Kala Award (separate ledger):
     Credit: kala:vendor:V1                  +10 kala
     Credit: kala:donor:D1                   +5 kala
     Type:   KALA_AWARD
```

### Example 2: Vendor Payouts

```
1. SLOW PAYOUT (free, scheduled)
   Vendor V1 earnings: $500

   TigerBeetle Transfer:
     Debit:  vendor:earnings:V1              $500
     Credit: community_bank_bridge           $500
     Type:   PAYOUT_SLOW

   External: ACH credit from community org to vendor GET card

2. FAST PAYOUT (instant, with fee)
   Vendor V1 requests instant payout: $200
   Fee: 1% = $2
   Rail cost: $1.50
   Platform margin: $0.50
   Vendor receives: $198

   TigerBeetle Transfer (atomic):
     Debit:  vendor:earnings:V1              $200.00
     Credit: community_bank_bridge           $198.00
     Credit: fees:payout_fast                $2.00
     Type:   PAYOUT_FAST

   External: Push-to-debit $198 to vendor GET card
```

### Example 3: Tax Payment

```
QUARTERLY GET PAYMENT
Vendor V1 tax reserve: $450
Filing period: Q4 2025

TigerBeetle Transfer:
  Debit:  vendor:tax_reserve:V1           $450
  Credit: community_bank_bridge           $450
  Type:   TAX_PAYMENT

External: ACH debit from vendor Tax Reserve account to HTO
HTO filing: Form G-45 with $450 payment
```

## Technology Stack

### Core Technologies

- **Ledger:** TigerBeetle (distributed financial database)
- **Orchestration:** TypeScript/Node.js microservices
- **API Layer:** GraphQL (Apollo Server) + REST
- **Database:** PostgreSQL (for non-ledger data: users, cards, configs)
- **Message Queue:** NATS or Kafka (for events, async processing)
- **Containerization:** Docker + Kubernetes

### External Integrations

- **Card Processor:** Marqeta, Stripe Issuing, or similar
- **ACH/RTP:** Plaid, Modern Treasury, or similar
- **Mojaloop:** Official Mojaloop SDK
- **Tax Filing:** Hawaiʻi Tax Online integration

## Security & Compliance

### Money Transmitter Avoidance

1. **No pooled funds:** All money belongs to individuals or community org
2. **No float:** Ledger balances are claims, not deposits
3. **KYC delegation:** Banks perform all KYC/CIP
4. **Limited entity:** Only community org has EIN; vendors use SSN

### Gift Card Compliance (FinCEN)

1. **Closed-loop:** Only usable at Ohana merchants
2. **Load limits:** ≤$2,000/day per card
3. **No cash access:** Except HI law <$5 redemption
4. **No P2P:** Cards cannot transfer to other consumers

### Tax Compliance (Hawaiʻi)

1. **GET collection:** Automatic 4.5% accrual on all sales
2. **Segregated reserves:** Vendor tax accounts separate from earnings
3. **Automated filing:** Integration with Hawaiʻi Tax Online
4. **Audit trail:** Full ledger history for tax authorities

### Data Security

1. **Credential vault:** Encrypted storage for vendor HTO credentials
2. **PCI compliance:** Card data handled by certified processor
3. **Audit logs:** Immutable TigerBeetle journal + PostgreSQL event log
4. **Access control:** Role-based permissions for all operations

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  TigerBeetle Cluster (3-node minimum)          │    │
│  │  - Node 1 (primary)                             │    │
│  │  - Node 2 (replica)                             │    │
│  │  - Node 3 (replica)                             │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Service Pods                                   │    │
│  │  - API Gateway (3 replicas)                     │    │
│  │  - Ledger Service (2 replicas)                  │    │
│  │  - Gift Card Service (2 replicas)               │    │
│  │  - Payout Orchestrator (2 replicas)             │    │
│  │  - Tax Orchestrator (1 replica)                 │    │
│  │  - Mojaloop Connector (2 replicas)              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  PostgreSQL (primary + replica)                 │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  NATS Streaming (messaging)                     │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

- **Metrics:** Prometheus + Grafana
- **Logging:** Structured logs → ELK stack
- **Tracing:** OpenTelemetry
- **Alerting:** Critical events (failed transfers, constraint violations, tax deadline misses)

## Next Steps

See implementation in:
- `/payment/services/` - Service implementations
- `/payment/models/` - Data models and schemas
- `/payment/integrations/` - External integration adapters
- `/payment/tests/` - Test suites
- `/payment/examples/` - Example flows and usage
