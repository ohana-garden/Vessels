# Vessels Neighborhood Payment Platform

An ethical, agentic payment and accounting platform for Hawaiʻi (Puna, Big Island) optimized for tiny vendors, kupuna, micro-farms, and home kitchens.

## Overview

Vessels is a **two-layer money system** that:
- Uses **existing fiat rails only** (USD) - no new token or crypto
- Integrates with **Mojaloop** for instant, low-fee transfers where available
- Keeps money movement **fully legal and compliant** in the U.S. and Hawaiʻi
- Maximizes **transparency, auditability, and user protection**
- Serves micro-vendors with low balances and minimal paperwork

## Core Components

### Platform Names

- **Overall platform**: Vessels
- **Vendor spending instrument**: GET Reserve Card
- **Vendor tax bucket instrument**: Tax Reserve Account / Card
- **Gift instrument**: Ohana Gift Card
- **Internal ledger + agents layer**: Ohana Ledger

### Two-Layer Architecture

**Layer 1: External Money Rails**
- Regular bank accounts (community org + vendors + households)
- Mojaloop-connected DFSPs (credit unions, wallet providers)
- ACH, RTP/FedNow, and card rails via payment processors

**Layer 2: Internal High-Resolution Ledger (TigerBeetle)**
- USD obligations (double-entry accounting)
- Kala participation metrics (NOT money, separate ledger)
- Hawaii GET tax accruals
- Gift card liabilities
- Full audit trail

## Key Features

### 1. Ohana Ledger (TigerBeetle)

High-performance distributed financial accounting database:
- Double-entry bookkeeping with strong consistency
- Separate ledgers for USD and Kala (never mixed)
- Idempotent, atomic transfers
- Full audit trail with immutable journal
- Microsecond latency

**Location:** `services/ohana-ledger.ts`

### 2. Ohana Gift Cards

Closed-loop prepaid system (FinCEN compliant):
- Usable only at Ohana merchant network
- Daily load limit ≤ $2,000 per card
- No ATM access except HI law <$5 cash redemption
- No P2P transfers
- Automatic GET accrual on every redemption

**Location:** `services/gift-card-service.ts`

### 3. Vendor Payouts

Two payout modes:
- **Slow (free)**: Standard ACH, 2-3 business days, no fee
- **Fast (with fee)**: Push-to-debit/RTP/FedNow, instant, vendor pays 1% or $0.50 minimum

**Location:** `services/payout-orchestrator.ts`

### 4. Hawaii GET Tax Automation

Automated General Excise Tax handling:
- 4.5% default rate (4% state + 0.5% county)
- Automatic accrual on every sale
- Segregated tax reserve accounts
- Automated filing with Hawaii Tax Online (HTO)
- ACH payment to HTO from tax reserves

**Location:** `services/tax-orchestrator.ts`

### 5. Mojaloop Integration

Instant payments between DFSPs:
- FSPIOP protocol implementation
- Quote, transfer, commit lifecycle
- Graceful fallback to ACH/card rails
- Fully encapsulated in connector service

**Location:** `services/mojaloop-connector.ts`

## Regulatory Compliance

### NOT a Money Transmitter

- No pooled omnibus customer funds
- All real funds belong to individuals or single community fund org
- KYC delegated to banks/DFSPs
- Ledger tracks obligations, not deposits

### Gift Card Compliance

- Closed-loop network exemption (FinCEN)
- Hawaii gift card law compliance (HRS § 481B-13)
- Daily load limits enforced

### Tax Compliance

- Automatic GET collection and segregation
- Automated filing with HTO
- Full audit trail for tax authorities
- 7-year record retention

**See:** `docs/SECURITY_AND_COMPLIANCE.md`

## Directory Structure

```
payment/
├── docs/
│   ├── ARCHITECTURE.md                  # System architecture overview
│   ├── API_SPECIFICATION.md             # GraphQL/REST API docs
│   └── SECURITY_AND_COMPLIANCE.md       # Regulatory compliance
├── models/
│   ├── schema.sql                       # PostgreSQL schema
│   └── tigerbeetle-schema.ts            # TigerBeetle types & helpers
├── services/
│   ├── ohana-ledger.ts                  # Core ledger service
│   ├── gift-card-service.ts             # Gift card operations
│   ├── payout-orchestrator.ts           # Vendor payouts
│   ├── tax-orchestrator.ts              # GET tax automation
│   └── mojaloop-connector.ts            # Mojaloop integration
├── integrations/
│   ├── ach-provider-stub.ts             # ACH provider adapter
│   ├── card-processor-stub.ts           # Card issuing adapter
│   ├── hawaii-tax-online-stub.ts        # HTO integration adapter
│   └── README.md                        # Integration documentation
├── examples/
│   └── end-to-end-flow.ts               # Complete lifecycle demo
└── tests/
    └── (test suites)
```

## Quick Start

### Prerequisites

- Node.js 18+
- PostgreSQL 14+
- TigerBeetle cluster (see [TigerBeetle docs](https://docs.tigerbeetle.com/))
- Docker (optional, for local development)

### Installation

```bash
# Install dependencies
npm install

# Set up PostgreSQL database
createdb vessels_payment
psql vessels_payment < payment/models/schema.sql

# Initialize TigerBeetle cluster
tigerbeetle format --cluster=0 --replica=0 --replica-count=1 0.tigerbeetle
tigerbeetle start --addresses=3000 0.tigerbeetle

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

### Configuration

```env
# Database
DATABASE_URL=postgresql://localhost/vessels_payment

# TigerBeetle
TIGERBEETLE_CLUSTER_IDS=0
TIGERBEETLE_REPLICAS=3000
COMMUNITY_ORG_ID=your-community-org-uuid

# External providers
ACH_PROVIDER=modern_treasury
ACH_API_KEY=your-key
CARD_PROCESSOR=marqeta
CARD_API_KEY=your-key
HTO_INTEGRATION_MODE=api
MOJALOOP_SWITCH_URL=https://mojaloop.hawaii.gov
```

### Run Example Flow

```bash
# Run complete end-to-end scenario
npm run example:flow

# Output shows:
# 1. Donor buys $100 gift card
# 2. Kupuna redeems at vendors
# 3. GET accrues automatically
# 4. Vendors request payouts
# 5. Tax filing and payment
```

## API Usage

### GraphQL API

```graphql
# Issue gift card
mutation IssueGiftCard {
  issueGiftCard(input: {
    initialBalanceUsd: 100.00
    donorActorId: "donor-uuid"
  }) {
    id
    cardToken
    currentBalance
  }
}

# Redeem gift card
mutation RedeemCard {
  redeemGiftCard(input: {
    cardToken: "CARD-TOKEN"
    vendorId: "vendor-uuid"
    amountUsd: 25.00
  }) {
    id
    amount
    vendor { businessName }
  }
}

# Request payout
mutation RequestPayout {
  requestPayout(input: {
    vendorId: "vendor-uuid"
    amountUsd: 200.00
    payoutType: FAST_FEE
  }) {
    id
    fee
    netToVendor
    status
  }
}
```

**See:** `docs/API_SPECIFICATION.md` for complete API documentation

## Data Model

### Key Entities

**PostgreSQL (Orchestration Data):**
- `actors` - People, vendors, households
- `vendors` - Business profiles, payout preferences
- `gift_cards` - Card metadata, balances (cached)
- `gift_card_transactions` - Redemption history
- `payouts` - Payout requests and status
- `tax_filings` - GET filing history
- `mojaloop_transfers` - Mojaloop transfer log

**TigerBeetle (Ledger Data):**
- Accounts: vendors, gift cards, community fund, fees
- Transfers: loads, redemptions, payouts, tax payments
- Separate USD and Kala ledgers

**See:** `models/schema.sql` and `models/tigerbeetle-schema.ts`

## Security

- **Authentication:** JWT tokens with MFA for sensitive operations
- **Encryption:** TLS 1.3 in transit, AES-256 at rest
- **Secrets:** HashiCorp Vault or AWS Secrets Manager
- **Audit:** Immutable TigerBeetle journal + PostgreSQL event log
- **Rate limiting:** 1000 req/hr per API key
- **PCI compliance:** Card data handled by certified processors only

**See:** `docs/SECURITY_AND_COMPLIANCE.md`

## Integration with Vessels Agent Platform

The payment platform integrates with the broader Vessels ethical agent framework:

### Kala Integration

- Participation metrics tracked separately from money
- Donors awarded Kala for gift card purchases
- Vendors awarded Kala for sales
- Kala visible in vendor dashboards
- Influences agent routing and priority

### Moral Constraint Integration

- All payment operations can be gated through Vessels constraint system
- Service virtue dimension influenced by benefit ratios
- Truthfulness enforced for tax reporting
- Detachment from money (Kala as alternative recognition)

### Community Memory

- Payment events stored in community memory
- Agents learn patterns (e.g., seasonal vendor activity)
- Tax filing best practices shared across vendors

## Deployment

### Production Checklist

- [ ] TigerBeetle cluster (3+ nodes, production config)
- [ ] PostgreSQL with replication
- [ ] External provider accounts (ACH, card processor, HTO)
- [ ] SSL certificates
- [ ] Monitoring and alerting setup
- [ ] Backup and disaster recovery plan
- [ ] Legal review of money transmitter exemption
- [ ] Compliance documentation updated

### Scaling

- **TigerBeetle**: Add replicas for read scaling
- **API services**: Horizontal scaling via Kubernetes
- **PostgreSQL**: Read replicas for reporting queries
- **Caching**: Redis for hot vendor balances

## Testing

```bash
# Run unit tests
npm test

# Run integration tests (requires TigerBeetle + PostgreSQL)
npm run test:integration

# Run end-to-end scenario
npm run example:flow

# Load testing
npm run test:load
```

## Roadmap

### Phase 1 (Current)
- ✅ Core ledger (TigerBeetle)
- ✅ Gift cards (closed-loop)
- ✅ Vendor payouts (slow/fast)
- ✅ GET tax automation
- ✅ Mojaloop connector

### Phase 2 (Next)
- [ ] Mobile app for vendors
- [ ] QR code redemption at vending machines
- [ ] Batch gift card issuance for donors
- [ ] Advanced tax reporting (1099-K)
- [ ] Multi-currency support (if Mojaloop expands)

### Phase 3 (Future)
- [ ] Vendor-to-vendor transfers
- [ ] Recurring gift card subscriptions
- [ ] Integration with local government benefits
- [ ] Cross-community Mojaloop network

## Contributing

### Development Setup

1. Fork repository
2. Create feature branch
3. Install dependencies: `npm install`
4. Run tests: `npm test`
5. Submit pull request

### Code Style

- TypeScript strict mode
- ESLint + Prettier
- Meaningful variable names
- Comprehensive error handling
- Unit tests for all business logic

## License

See LICENSE file.

## Support

- **Documentation:** https://docs.vessels.ohana/payment
- **Issues:** https://github.com/ohana-garden/vessels/issues
- **Email:** support@vessels.ohana
- **Compliance:** compliance@vessels.ohana

## Acknowledgments

- **TigerBeetle:** For providing world-class financial accounting infrastructure
- **Mojaloop Foundation:** For open financial interoperability standards
- **Hawaii community:** For inspiring ethical, local-first commerce

---

**Built with aloha for Puna, Hawaiʻi** 🌺

*Vessels: Money that moves like water, values that anchor like stone.*
