# Vessels Payment Platform API Specification

## Overview

GraphQL API for the Vessels neighborhood payment platform.
Base URL: `https://api.vessels.ohana/graphql`

## Authentication

All requests require Bearer token authentication:
```
Authorization: Bearer <JWT_TOKEN>
```

Tokens contain:
- `actor_id`: UUID of authenticated actor
- `role`: `vendor` | `community_admin` | `donor`
- `permissions`: Array of permission strings

## GraphQL Schema

### Types

```graphql
# ============================================================================
# SCALARS
# ============================================================================

scalar DateTime
scalar BigInt
scalar USD  # Decimal with 2 decimal places

# ============================================================================
# ENUMS
# ============================================================================

enum GiftCardStatus {
  PENDING_ACTIVATION
  ACTIVE
  SUSPENDED
  DEPLETED
  EXPIRED
}

enum PayoutType {
  SLOW_FREE
  FAST_FEE
}

enum PayoutStatus {
  PENDING
  PROCESSING
  COMPLETED
  FAILED
  CANCELLED
}

enum FilingFrequency {
  MONTHLY
  QUARTERLY
  SEMIANNUAL
  ANNUAL
}

enum FilingStatus {
  SCHEDULED
  PROCESSING
  FILED
  FAILED
  AMENDED
}

# ============================================================================
# VENDOR TYPES
# ============================================================================

type Vendor {
  id: ID!
  actor: Actor!
  businessName: String!
  businessDescription: String
  status: String!
  getRate: Float!
  filingFrequency: FilingFrequency!
  nextFilingDate: DateTime

  # Balances
  earnings: VendorBalance!
  taxReserve: VendorBalance!
  kala: VendorBalance!

  # History
  payouts(limit: Int = 50): [Payout!]!
  taxFilings(limit: Int = 12): [TaxFiling!]!

  createdAt: DateTime!
  updatedAt: DateTime!
}

type VendorBalance {
  usd: USD
  kala: BigInt
  debitsPosted: BigInt
  creditsPosted: BigInt
}

# ============================================================================
# GIFT CARD TYPES
# ============================================================================

type GiftCard {
  id: ID!
  cardToken: String!
  status: GiftCardStatus!
  currentBalance: USD!
  originalBalance: USD!
  dailyLoadLimit: USD!
  owner: Actor
  donor: Actor
  issuedAt: DateTime
  expiresAt: DateTime
  lastUsedAt: DateTime
  transactions(limit: Int = 50): [GiftCardTransaction!]!
}

type GiftCardTransaction {
  id: ID!
  transactionType: String!
  amount: USD!
  vendor: Vendor
  location: String
  createdAt: DateTime!
}

# ============================================================================
# PAYOUT TYPES
# ============================================================================

type Payout {
  id: ID!
  vendor: Vendor!
  payoutType: PayoutType!
  amount: USD!
  fee: USD!
  netToVendor: USD!
  status: PayoutStatus!
  requestedAt: DateTime!
  completedAt: DateTime
  errorMessage: String
}

type PayoutQuote {
  amount: USD!
  fee: USD!
  netToVendor: USD!
  estimatedDelivery: String!
}

# ============================================================================
# TAX TYPES
# ============================================================================

type TaxFiling {
  id: ID!
  vendor: Vendor!
  periodStart: DateTime!
  periodEnd: DateTime!
  grossReceipts: USD!
  getRate: Float!
  getDue: USD!
  status: FilingStatus!
  dueDate: DateTime!
  filedAt: DateTime
  htoConfirmationNumber: String
}

type TaxSummary {
  grossReceipts: USD!
  getDue: USD!
  periodStart: DateTime!
  periodEnd: DateTime!
}

# ============================================================================
# ACTOR TYPES
# ============================================================================

type Actor {
  id: ID!
  actorType: String!
  name: String!
  email: String
}

# ============================================================================
# QUERIES
# ============================================================================

type Query {
  # Vendor queries
  vendor(id: ID!): Vendor
  me: Vendor  # Current authenticated vendor

  # Gift card queries
  giftCard(cardToken: String!): GiftCard
  giftCardBalance(cardToken: String!): USD!

  # Payout queries
  payout(id: ID!): Payout
  payoutQuote(amountUsd: USD!, type: PayoutType!): PayoutQuote!

  # Tax queries
  taxFiling(id: ID!): TaxFiling
  taxSummary(vendorId: ID!, periodStart: DateTime!, periodEnd: DateTime!): TaxSummary!
}

# ============================================================================
# MUTATIONS
# ============================================================================

type Mutation {
  # Vendor operations
  createVendor(input: CreateVendorInput!): Vendor!
  updateVendor(id: ID!, input: UpdateVendorInput!): Vendor!

  # Gift card operations
  issueGiftCard(input: IssueGiftCardInput!): GiftCard!
  loadGiftCard(cardToken: String!, amountUsd: USD!): GiftCardTransaction!
  redeemGiftCard(input: RedeemGiftCardInput!): GiftCardTransaction!
  cashOutGiftCard(cardToken: String!): GiftCardTransaction!

  # Payout operations
  requestPayout(input: RequestPayoutInput!): Payout!

  # Tax operations
  scheduleTaxFiling(input: ScheduleTaxFilingInput!): TaxFiling!
  fileAndPayGET(filingId: ID!): TaxFiling!
}

# ============================================================================
# INPUT TYPES
# ============================================================================

input CreateVendorInput {
  actorId: ID!
  businessName: String!
  businessDescription: String
  getCardProgramId: String!
  taxReserveAccountId: String!
  getRate: Float
  filingFrequency: FilingFrequency!
}

input UpdateVendorInput {
  businessName: String
  businessDescription: String
  filingFrequency: FilingFrequency
}

input IssueGiftCardInput {
  initialBalanceUsd: USD!
  donorActorId: ID!
  ownerActorId: ID
  expiresAt: DateTime
}

input RedeemGiftCardInput {
  cardToken: String!
  vendorId: ID!
  amountUsd: USD!
  location: String
}

input RequestPayoutInput {
  vendorId: ID!
  amountUsd: USD!
  payoutType: PayoutType!
}

input ScheduleTaxFilingInput {
  vendorId: ID!
  periodStart: DateTime!
  periodEnd: DateTime!
  dueDate: DateTime!
  filingFrequency: FilingFrequency!
}
```

## Example Queries

### Get Vendor Dashboard

```graphql
query VendorDashboard {
  me {
    id
    businessName
    earnings {
      usd
    }
    taxReserve {
      usd
    }
    kala {
      kala
    }
    payouts(limit: 10) {
      id
      amount
      fee
      status
      requestedAt
    }
    taxFilings(limit: 4) {
      id
      periodStart
      periodEnd
      getDue
      status
      dueDate
    }
  }
}
```

### Get Gift Card Balance

```graphql
query GiftCardBalance($cardToken: String!) {
  giftCard(cardToken: $cardToken) {
    currentBalance
    status
    transactions(limit: 10) {
      transactionType
      amount
      vendor {
        businessName
      }
      createdAt
    }
  }
}
```

### Request Payout Quote

```graphql
query PayoutQuote($amount: USD!, $type: PayoutType!) {
  payoutQuote(amountUsd: $amount, type: $type) {
    amount
    fee
    netToVendor
    estimatedDelivery
  }
}
```

## Example Mutations

### Issue Gift Card

```graphql
mutation IssueGiftCard($input: IssueGiftCardInput!) {
  issueGiftCard(input: $input) {
    id
    cardToken
    currentBalance
    status
  }
}

# Variables:
{
  "input": {
    "initialBalanceUsd": 100.00,
    "donorActorId": "123e4567-e89b-12d3-a456-426614174000"
  }
}
```

### Redeem Gift Card

```graphql
mutation RedeemGiftCard($input: RedeemGiftCardInput!) {
  redeemGiftCard(input: $input) {
    id
    amount
    vendor {
      businessName
    }
    createdAt
  }
}

# Variables:
{
  "input": {
    "cardToken": "A1B2C3D4E5F6",
    "vendorId": "vendor-uuid",
    "amountUsd": 10.50,
    "location": "Puna Farmers Market"
  }
}
```

### Request Fast Payout

```graphql
mutation RequestPayout($input: RequestPayoutInput!) {
  requestPayout(input: $input) {
    id
    amount
    fee
    netToVendor
    status
    requestedAt
  }
}

# Variables:
{
  "input": {
    "vendorId": "vendor-uuid",
    "amountUsd": 200.00,
    "payoutType": FAST_FEE
  }
}
```

### File and Pay GET

```graphql
mutation FileGET($filingId: ID!) {
  fileAndPayGET(filingId: $filingId) {
    id
    status
    htoConfirmationNumber
    filedAt
  }
}
```

## REST Endpoints (Webhooks & Callbacks)

### POST /webhooks/mojaloop/transfer-callback

Receive transfer commit callback from Mojaloop switch.

**Request:**
```json
{
  "transferId": "ml-uuid",
  "fulfilment": "base64-encoded-fulfilment",
  "transferState": "COMMITTED"
}
```

**Response:**
```json
{
  "status": "accepted"
}
```

### POST /webhooks/hto/payment-confirmation

Receive payment confirmation from Hawaii Tax Online.

**Request:**
```json
{
  "confirmationNumber": "HTO-12345",
  "amountPaid": 45.00,
  "paymentDate": "2025-11-22T10:30:00Z"
}
```

**Response:**
```json
{
  "status": "confirmed"
}
```

## Error Handling

### Error Response Format

```json
{
  "errors": [
    {
      "message": "Insufficient card balance",
      "extensions": {
        "code": "INSUFFICIENT_BALANCE",
        "availableBalance": 5.00,
        "requestedAmount": 10.00
      }
    }
  ]
}
```

### Error Codes

- `INSUFFICIENT_BALANCE`: Not enough funds
- `DAILY_LIMIT_EXCEEDED`: Gift card daily load limit exceeded
- `CARD_NOT_FOUND`: Gift card token invalid
- `VENDOR_NOT_FOUND`: Vendor ID invalid
- `UNAUTHORIZED`: Missing or invalid authentication
- `FORBIDDEN`: Insufficient permissions
- `VALIDATION_ERROR`: Input validation failed
- `EXTERNAL_SERVICE_ERROR`: External provider (ACH, HTO, etc.) failed

## Rate Limiting

- 1000 requests per hour per API key
- 100 requests per minute per endpoint
- Response headers:
  - `X-RateLimit-Limit`: Total limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

## Pagination

Use `limit` and `offset` for paginated queries:

```graphql
query VendorPayouts {
  me {
    payouts(limit: 20, offset: 0) {
      id
      amount
      status
    }
  }
}
```

## Subscriptions (Future)

Real-time updates via WebSocket subscriptions:

```graphql
subscription OnPayoutStatusChange($vendorId: ID!) {
  payoutStatusChanged(vendorId: $vendorId) {
    id
    status
    completedAt
  }
}
```
