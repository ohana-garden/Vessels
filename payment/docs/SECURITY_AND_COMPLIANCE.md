# Security and Compliance Documentation

## Overview

The Vessels payment platform is designed to be **fully legal and compliant** while serving micro-vendors, kupuna, and community members with minimal paperwork.

## Regulatory Compliance

### 1. Money Transmitter Exemption

**How Vessels Avoids Being a Money Transmitter:**

#### No Pooled Customer Funds
- All real USD belongs to either:
  - **Individual humans** (vendors, households), OR
  - **Single community fund organization** (nonprofit/coop with EIN)
- NO omnibus accounts holding commingled customer funds

#### Ledger as Claims System
- TigerBeetle ledger tracks **obligations**, not deposits
- Vendor "balances" represent:
  - Amounts owed by community org to vendor
  - NOT money held in custody for vendor
- Actual money sits in:
  - Community org's bank account, OR
  - Vendor's own GET Reserve Card account

#### External Money Movement Only
- Vessels NEVER holds money between parties
- All transfers occur through:
  - Licensed banks (ACH, wire)
  - Card networks (push-to-debit)
  - Mojaloop-connected DFSPs
- Vessels orchestrates, does NOT transmit

#### Single Entity Model
- Only ONE entity with EIN: community fund organization
- Vendors are sole proprietors using SSN (where allowed)
- No multi-entity money pooling

**Legal Basis:**
- Safe harbor under [31 CFR 1010.100(ff)(5)(ii)(F)]: Transactions within closed network
- Agent of payee model: Community org acts on behalf of vendors
- No value-for-value exchange outside network

### 2. KYC/AML Compliance

**Delegation to Banks:**

All Know Your Customer (KYC) and Customer Identification Program (CIP) requirements are delegated to:

1. **Banks issuing GET Reserve Cards**
   - Perform full KYC on vendors
   - Verify identity (SSN/EIN)
   - OFAC screening
   - Ongoing monitoring

2. **Banks issuing Tax Reserve Accounts**
   - Same KYC as above
   - May be same institution as GET card

3. **Mojaloop DFSPs**
   - Each DFSP performs own KYC
   - Vessels trusts DFSP participant registration

**What Vessels Stores:**
- Minimal PII for linking accounts:
  - Name
  - Email
  - Hashed SSN/EIN (never plaintext)
  - External account tokens/IDs
- NO full KYC documents
- NO identity verification performed by Vessels

**Suspicious Activity Monitoring:**
- Banks perform SAR filing, not Vessels
- Vessels logs all transactions for audit
- Anomaly detection for:
  - Rapid redemption patterns
  - Unusual payout requests
  - GET ratio anomalies

### 3. Gift Card Compliance (FinCEN Prepaid Access)

**Closed-Loop Prepaid Design:**

Ohana Gift Cards comply with FinCEN prepaid access rules by being **closed-loop**:

#### Restrictions
- ✓ Usable ONLY at Ohana merchant network (local vendors)
- ✓ Cannot be used at non-participating merchants
- ✓ No ATM cash access (except HI law <$5 redemption)
- ✓ No P2P transfer between cardholders
- ✓ Daily load limit ≤ $2,000 per card
- ✓ No reloadable after depletion (new card required)

#### Exemptions Applied
- Closed-loop network with ≤200 locations: **Exempt from registration**
- No cross-border use: **Exempt from enhanced due diligence**
- No convertibility to cash: **Exempt from cash access provisions**

#### Hawaii State Law Compliance
- **HRS § 481B-13**: Gift card balance <$5 redeemable in cash
  - Implemented via `cashOutGiftCard()` method
  - Logged as `GIFT_CARD_CASHOUT` transfer
- No expiration fees (cards may expire, but no fees charged)
- Clear terms disclosed at purchase

**Legal Basis:**
- 31 CFR § 1022.210(e): Closed-loop exclusion
- Safe harbor for intra-network stored value

### 4. Hawaii GET (General Excise Tax) Compliance

**Tax Collection & Remittance:**

#### Automatic Accrual
- Every sale automatically splits:
  - Net earnings → vendor earnings account
  - GET portion → vendor tax reserve account
- Default rate: 4.5% (4% state + 0.5% county)
- Rate configurable per vendor (different islands/activities)

#### Segregated Reserves
- Tax reserve accounts are **conceptually locked**
- Vendors cannot spend tax reserves (separate card)
- Only used for:
  - Automated GET payments to HTO
  - Manual vendor override (discouraged, flagged)

#### Automated Filing
- Tax Orchestrator tracks vendor filing frequency:
  - Monthly (gross receipts >$4,000/mo)
  - Quarterly (default)
  - Semiannual
  - Annual (gross receipts <$1,000/yr)
- Generates Form G-45 data
- Files electronically via Hawaii Tax Online (HTO)
- Initiates ACH debit from tax reserve account

#### Audit Trail
- Full double-entry ledger in TigerBeetle
- PostgreSQL records:
  - Each sale with GET calculation
  - Each filing with gross receipts
  - HTO confirmation numbers
- Exportable for tax audits

**Legal Basis:**
- HRS § 237: General Excise Tax Law
- HAR § 18-237: Tax filing requirements
- Compliance with HTO electronic filing mandates

### 5. Data Privacy & Protection

#### GDPR/CCPA Considerations
- Minimal data collection (privacy by design)
- Right to access: API for users to export data
- Right to deletion: Soft delete (preserve audit trail)
- Data retention: 7 years (IRS/GET requirements)

#### PCI DSS Compliance
- Card data (PAN) NEVER stored by Vessels
- Card processor handles all PCI-regulated data
- Vessels stores only:
  - Tokenized references
  - Last 4 digits (display only)
  - Program IDs (non-sensitive)

#### Data Encryption
- At rest: AES-256 encryption for PostgreSQL
- In transit: TLS 1.3 for all API calls
- Secrets: HashiCorp Vault or AWS Secrets Manager
- Credential rotation: Every 90 days

### 6. Financial Audit & Reporting

#### Double-Entry Integrity
- TigerBeetle provides:
  - Strong consistency (linearizable)
  - Immutable journal (append-only)
  - Account balances always balanced
- Audit query: Sum(debits) = Sum(credits) across all accounts

#### Reconciliation
- Daily: TigerBeetle balances vs external bank balances
- Weekly: Gift card liabilities vs issued cards
- Monthly: Vendor earnings vs payouts + tax reserves
- Quarterly: GET accrued vs GET paid to HTO

#### External Auditor Access
- Read-only PostgreSQL replica
- TigerBeetle query API for ledger inspection
- Exportable CSV/JSON reports
- Timestamped, cryptographically signed logs

#### Regulatory Filings
- Annual 1099-K for vendors (>$600 earnings)
- Hawaii GET filings (automated)
- Transaction records retained 7 years

## Security Measures

### 1. Authentication & Authorization

**Actor Authentication:**
- JWT tokens with short expiry (15 min)
- Refresh tokens (7 days, rotated)
- MFA required for:
  - Community admin accounts
  - Large payouts (>$500)
  - Tax payment approvals

**Authorization Model:**
- Role-based access control (RBAC)
- Roles:
  - `vendor`: Own account access only
  - `community_admin`: Platform-wide read, vendor support
  - `system`: Internal service-to-service
- Permissions:
  - `read:own_vendor`
  - `write:own_vendor`
  - `read:all_vendors` (admin only)
  - `payout:request`
  - `tax:file`

### 2. API Security

**Rate Limiting:**
- 1,000 requests/hour per API key
- 100 requests/minute per endpoint
- Burst allowance: 10 requests/second (30 second window)

**Input Validation:**
- Schema validation (GraphQL types)
- Amount limits:
  - Gift card load: ≤$2,000/day
  - Payout: ≥$1, ≤vendor balance
  - All USD amounts: 2 decimal places
- String sanitization (SQL injection prevention)

**Output Encoding:**
- JSON escaping
- No raw SQL in error messages
- Redact sensitive data in logs

### 3. Infrastructure Security

**Network Security:**
- VPC isolation for TigerBeetle cluster
- Private subnets for databases
- Load balancer with WAF (Web Application Firewall)
- DDoS protection (Cloudflare / AWS Shield)

**Secrets Management:**
- No secrets in code or env files
- HashiCorp Vault or AWS Secrets Manager
- Automatic rotation:
  - API keys: 90 days
  - Database passwords: 30 days
  - JWT signing keys: 7 days

**Monitoring & Alerting:**
- Prometheus metrics:
  - Transfer success/failure rates
  - Ledger balance discrepancies
  - API latency (p50, p95, p99)
- Alerts for:
  - Failed transfers (>1% error rate)
  - Unbalanced ledger
  - Suspicious activity patterns
  - External service downtime

### 4. Incident Response

**Security Events:**
- Logged to immutable append-only log
- Security event types:
  - `failed_authentication`
  - `authorization_denied`
  - `suspicious_redemption_pattern`
  - `payout_limit_exceeded`
  - `ledger_balance_mismatch`

**Incident Playbooks:**
1. **Compromised API Key**
   - Revoke key immediately
   - Audit recent requests
   - Notify affected users
   - Rotate secrets

2. **Failed Transfer**
   - Check TigerBeetle logs
   - Verify account balances
   - Retry if idempotent
   - Manual reversal if needed

3. **External Service Outage**
   - Activate circuit breaker
   - Queue requests for retry
   - Notify users of delay
   - Escalate if >1 hour

## Compliance Attestations

### Annual Reviews
- External security audit (penetration testing)
- Financial audit of ledger integrity
- Legal review of money transmitter exemption
- PCI DSS assessment (if applicable)

### Documentation
- This security & compliance document
- API documentation with auth requirements
- Incident response runbooks
- Data retention policy
- Privacy policy (user-facing)

### Certifications
- SOC 2 Type II (target: Year 2)
- ISO 27001 (target: Year 3)

## User Protection

### Vendor Protections
1. **Transparent accounting**: Full ledger access via API
2. **Earnings isolation**: Tax reserves cannot be spent
3. **Automated tax filing**: No missed deadlines
4. **Multiple payout options**: Slow (free) or fast (fee)

### Donor Protections
1. **Gift card guarantees**: Value honored by network
2. **Usage transparency**: Donors can track gift card use
3. **Kala recognition**: Non-monetary contribution tracking

### Community Protections
1. **Open audit logs**: Anyone can verify integrity
2. **No hidden fees**: All costs disclosed upfront
3. **Ethical constraints**: Vessels agent layer enforces virtue constraints

## Compliance Contact

For regulatory inquiries or compliance questions:
- Email: compliance@vessels.ohana
- Documentation: https://docs.vessels.ohana/compliance
- Audit requests: auditor-access@vessels.ohana

---

**Last Updated:** 2025-11-22
**Next Review:** 2026-05-22 (6 months)
**Version:** 1.0.0
