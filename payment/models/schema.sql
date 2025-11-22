-- Vessels Payment Platform Database Schema
-- PostgreSQL schema for orchestration data (non-ledger)
-- TigerBeetle handles all ledger/accounting data

-- ============================================================================
-- ACTORS: People, Organizations, Households
-- ============================================================================

CREATE TYPE actor_type AS ENUM (
    'person',
    'household',
    'vendor',
    'community_org',
    'donor'
);

CREATE TYPE identity_type AS ENUM (
    'ssn',      -- Sole proprietor
    'ein'       -- Incorporated entity
);

CREATE TABLE actors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_type actor_type NOT NULL,
    name VARCHAR(255) NOT NULL,

    -- Identity (minimal - KYC handled by banks)
    identity_type identity_type,
    identity_hash VARCHAR(64),  -- Hashed SSN/EIN, never plain text

    -- Contact
    email VARCHAR(255),
    phone VARCHAR(20),

    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state CHAR(2) DEFAULT 'HI',
    zip VARCHAR(10),

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT unique_identity UNIQUE (identity_type, identity_hash)
);

CREATE INDEX idx_actors_type ON actors(actor_type);
CREATE INDEX idx_actors_email ON actors(email);
CREATE INDEX idx_actors_active ON actors(is_active);

-- ============================================================================
-- VENDORS: Micro-businesses in the network
-- ============================================================================

CREATE TYPE vendor_status AS ENUM (
    'onboarding',
    'active',
    'suspended',
    'inactive'
);

CREATE TYPE filing_frequency AS ENUM (
    'monthly',
    'quarterly',
    'semiannual',
    'annual'
);

CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NOT NULL REFERENCES actors(id) ON DELETE CASCADE,

    -- Business info
    business_name VARCHAR(255) NOT NULL,
    business_description TEXT,
    business_type VARCHAR(100),  -- e.g., 'home_kitchen', 'micro_farm', 'craft_vendor'

    -- Status
    status vendor_status NOT NULL DEFAULT 'onboarding',

    -- GET Reserve Card (vendor spending account)
    get_card_program_id VARCHAR(100),  -- External card processor ID
    get_card_last_four CHAR(4),
    get_card_status VARCHAR(50),

    -- Tax Reserve Account/Card
    tax_reserve_account_id VARCHAR(100),  -- External account ID
    tax_reserve_last_four CHAR(4),
    tax_reserve_status VARCHAR(50),

    -- Hawaii GET tax settings
    get_rate DECIMAL(5,4) NOT NULL DEFAULT 0.0450,  -- 4.5% default (4% state + 0.5% county)
    filing_frequency filing_frequency NOT NULL DEFAULT 'quarterly',
    next_filing_date DATE,

    -- TigerBeetle account IDs (for reference)
    tb_earnings_account_id BIGINT,  -- vendor:earnings:VENDOR_ID
    tb_tax_reserve_account_id BIGINT,  -- vendor:tax_reserve:VENDOR_ID
    tb_kala_account_id BIGINT,  -- kala:vendor:VENDOR_ID

    -- Payout preferences
    payout_schedule VARCHAR(50) DEFAULT 'weekly',  -- 'daily', 'weekly', 'biweekly', 'monthly'
    payout_threshold_usd DECIMAL(10,2) DEFAULT 10.00,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    onboarded_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT unique_vendor_actor UNIQUE (actor_id)
);

CREATE INDEX idx_vendors_status ON vendors(status);
CREATE INDEX idx_vendors_filing_frequency ON vendors(filing_frequency);
CREATE INDEX idx_vendors_next_filing ON vendors(next_filing_date);
CREATE INDEX idx_vendors_get_card ON vendors(get_card_program_id);

-- ============================================================================
-- GIFT CARDS: Ohana Gift Cards (closed-loop prepaid)
-- ============================================================================

CREATE TYPE gift_card_status AS ENUM (
    'pending_activation',
    'active',
    'suspended',
    'depleted',
    'expired'
);

CREATE TABLE gift_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Card identifiers
    card_number VARCHAR(100) NOT NULL UNIQUE,  -- Tokenized, not real PAN
    card_token VARCHAR(100) NOT NULL UNIQUE,   -- For QR/NFC redemption

    -- Ownership
    owner_actor_id UUID REFERENCES actors(id),  -- Holder
    donor_actor_id UUID REFERENCES actors(id),  -- Original purchaser

    -- Status
    status gift_card_status NOT NULL DEFAULT 'pending_activation',

    -- Balance (cached from TigerBeetle)
    current_balance_usd DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    original_balance_usd DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    -- TigerBeetle account ID
    tb_liability_account_id BIGINT NOT NULL,  -- gift_card_liability:CARD_ID

    -- Limits (FinCEN compliance)
    daily_load_limit_usd DECIMAL(10,2) NOT NULL DEFAULT 2000.00,

    -- Dates
    issued_at TIMESTAMPTZ,
    activated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,  -- Optional expiration
    last_used_at TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT positive_balance CHECK (current_balance_usd >= 0)
);

CREATE INDEX idx_gift_cards_status ON gift_cards(status);
CREATE INDEX idx_gift_cards_owner ON gift_cards(owner_actor_id);
CREATE INDEX idx_gift_cards_donor ON gift_cards(donor_actor_id);
CREATE INDEX idx_gift_cards_token ON gift_cards(card_token);

-- ============================================================================
-- GIFT CARD TRANSACTIONS (audit log)
-- ============================================================================

CREATE TYPE card_transaction_type AS ENUM (
    'load',
    'redemption',
    'cashout',
    'refund',
    'adjustment'
);

CREATE TABLE gift_card_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gift_card_id UUID NOT NULL REFERENCES gift_cards(id),

    -- Transaction details
    transaction_type card_transaction_type NOT NULL,
    amount_usd DECIMAL(10,2) NOT NULL,

    -- Vendor (for redemptions)
    vendor_id UUID REFERENCES vendors(id),

    -- TigerBeetle transfer ID (idempotency key)
    tb_transfer_id BIGINT NOT NULL UNIQUE,

    -- Location/context
    location_description VARCHAR(255),

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT positive_amount CHECK (amount_usd > 0)
);

CREATE INDEX idx_card_txns_card ON gift_card_transactions(gift_card_id);
CREATE INDEX idx_card_txns_vendor ON gift_card_transactions(vendor_id);
CREATE INDEX idx_card_txns_type ON gift_card_transactions(transaction_type);
CREATE INDEX idx_card_txns_created ON gift_card_transactions(created_at DESC);

-- ============================================================================
-- DAILY LOAD TRACKING (FinCEN compliance)
-- ============================================================================

CREATE TABLE gift_card_daily_loads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gift_card_id UUID NOT NULL REFERENCES gift_cards(id),
    load_date DATE NOT NULL,
    total_loaded_usd DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    load_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_card_date UNIQUE (gift_card_id, load_date),
    CONSTRAINT positive_load CHECK (total_loaded_usd >= 0)
);

CREATE INDEX idx_daily_loads_card_date ON gift_card_daily_loads(gift_card_id, load_date DESC);

-- ============================================================================
-- PAYOUTS: Vendor payout requests and history
-- ============================================================================

CREATE TYPE payout_type AS ENUM (
    'slow_free',      -- Standard ACH, no fee
    'fast_fee'        -- Instant (RTP/push-to-debit), vendor pays fee
);

CREATE TYPE payout_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE payout_rail AS ENUM (
    'ach_standard',
    'ach_same_day',
    'rtp',
    'fednow',
    'push_to_debit'
);

CREATE TABLE payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id UUID NOT NULL REFERENCES vendors(id),

    -- Payout details
    payout_type payout_type NOT NULL,
    amount_usd DECIMAL(10,2) NOT NULL,
    fee_usd DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    net_to_vendor_usd DECIMAL(10,2) NOT NULL,

    -- Rail used
    payout_rail payout_rail NOT NULL,
    rail_cost_usd DECIMAL(10,2) NOT NULL DEFAULT 0.00,  -- What we paid to rail provider

    -- Status
    status payout_status NOT NULL DEFAULT 'pending',

    -- TigerBeetle transfer ID
    tb_transfer_id BIGINT UNIQUE,

    -- External provider details
    external_provider VARCHAR(100),  -- 'plaid', 'modern_treasury', etc.
    external_transaction_id VARCHAR(255),

    -- Timing
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,

    CONSTRAINT positive_amount CHECK (amount_usd > 0),
    CONSTRAINT valid_net CHECK (net_to_vendor_usd = amount_usd - fee_usd)
);

CREATE INDEX idx_payouts_vendor ON payouts(vendor_id);
CREATE INDEX idx_payouts_status ON payouts(status);
CREATE INDEX idx_payouts_requested ON payouts(requested_at DESC);
CREATE INDEX idx_payouts_type ON payouts(payout_type);

-- ============================================================================
-- TAX FILINGS: Hawaii GET filing history
-- ============================================================================

CREATE TYPE filing_status AS ENUM (
    'scheduled',
    'processing',
    'filed',
    'failed',
    'amended'
);

CREATE TABLE tax_filings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id UUID NOT NULL REFERENCES vendors(id),

    -- Filing period
    filing_period_start DATE NOT NULL,
    filing_period_end DATE NOT NULL,
    filing_frequency filing_frequency NOT NULL,

    -- Tax calculation
    gross_receipts_usd DECIMAL(12,2) NOT NULL,
    get_rate DECIMAL(5,4) NOT NULL,
    get_due_usd DECIMAL(12,2) NOT NULL,

    -- Status
    status filing_status NOT NULL DEFAULT 'scheduled',

    -- TigerBeetle transfer ID (tax payment)
    tb_transfer_id BIGINT UNIQUE,

    -- Hawaii Tax Online (HTO) details
    hto_confirmation_number VARCHAR(100),
    hto_filed_at TIMESTAMPTZ,

    -- Timing
    due_date DATE NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    filed_at TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,

    CONSTRAINT positive_receipts CHECK (gross_receipts_usd >= 0),
    CONSTRAINT positive_get CHECK (get_due_usd >= 0)
);

CREATE INDEX idx_filings_vendor ON tax_filings(vendor_id);
CREATE INDEX idx_filings_period ON tax_filings(filing_period_start, filing_period_end);
CREATE INDEX idx_filings_due_date ON tax_filings(due_date);
CREATE INDEX idx_filings_status ON tax_filings(status);

-- ============================================================================
-- MOJALOOP PARTICIPANTS
-- ============================================================================

CREATE TYPE participant_type AS ENUM (
    'dfsp',           -- Digital Financial Service Provider
    'hub',
    'switch'
);

CREATE TYPE participant_status AS ENUM (
    'pending',
    'active',
    'suspended',
    'inactive'
);

CREATE TABLE mojaloop_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Mojaloop identifiers
    participant_id VARCHAR(100) NOT NULL UNIQUE,  -- FSP ID in Mojaloop
    participant_name VARCHAR(255) NOT NULL,
    participant_type participant_type NOT NULL,

    -- Status
    status participant_status NOT NULL DEFAULT 'pending',

    -- TigerBeetle bridge account
    tb_bridge_account_id BIGINT,

    -- Endpoints
    callback_url VARCHAR(500),

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_mojaloop_participants_status ON mojaloop_participants(status);

-- ============================================================================
-- MOJALOOP TRANSFERS (audit log)
-- ============================================================================

CREATE TYPE mojaloop_transfer_status AS ENUM (
    'received',
    'reserved',
    'committed',
    'aborted',
    'timeout'
);

CREATE TABLE mojaloop_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Mojaloop transfer ID
    mojaloop_transfer_id VARCHAR(100) NOT NULL UNIQUE,

    -- Parties
    payer_fsp VARCHAR(100) NOT NULL,
    payee_fsp VARCHAR(100) NOT NULL,

    -- Amount
    amount_usd DECIMAL(10,2) NOT NULL,
    currency CHAR(3) DEFAULT 'USD',

    -- Status
    status mojaloop_transfer_status NOT NULL,

    -- TigerBeetle transfer ID
    tb_transfer_id BIGINT UNIQUE,

    -- Timing
    quote_at TIMESTAMPTZ,
    prepared_at TIMESTAMPTZ,
    committed_at TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT positive_amount CHECK (amount_usd > 0)
);

CREATE INDEX idx_mojaloop_transfers_status ON mojaloop_transfers(status);
CREATE INDEX idx_mojaloop_transfers_payer ON mojaloop_transfers(payer_fsp);
CREATE INDEX idx_mojaloop_transfers_payee ON mojaloop_transfers(payee_fsp);

-- ============================================================================
-- AUDIT LOG: All system events
-- ============================================================================

CREATE TYPE event_severity AS ENUM (
    'info',
    'warning',
    'error',
    'critical'
);

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event details
    event_type VARCHAR(100) NOT NULL,  -- 'gift_card.loaded', 'payout.completed', etc.
    event_severity event_severity NOT NULL DEFAULT 'info',

    -- Actor
    actor_id UUID REFERENCES actors(id),
    actor_type VARCHAR(50),

    -- Entity affected
    entity_type VARCHAR(50),  -- 'gift_card', 'vendor', 'payout', etc.
    entity_id UUID,

    -- Details
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Context
    ip_address INET,
    user_agent TEXT,

    -- Timing
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_log_severity ON audit_log(event_severity);
CREATE INDEX idx_audit_log_actor ON audit_log(actor_id);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at DESC);

-- ============================================================================
-- CONFIGURATIONS: System-wide settings
-- ============================================================================

CREATE TABLE configurations (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES actors(id)
);

-- Insert default configurations
INSERT INTO configurations (key, value, description) VALUES
    ('hawaii_get.default_rate', '0.0450', 'Default Hawaii GET rate (4% state + 0.5% county)'),
    ('gift_card.daily_load_limit', '2000.00', 'FinCEN compliance: max $2,000/day per card'),
    ('gift_card.cashout_threshold', '5.00', 'Hawaii law: allow cash redemption below $5'),
    ('payout.slow.schedule', '"weekly"', 'Default schedule for slow payouts'),
    ('payout.slow.threshold', '10.00', 'Minimum balance for slow payout'),
    ('payout.fast.fee_percentage', '0.01', 'Fast payout fee: 1% of amount'),
    ('payout.fast.fee_minimum', '0.50', 'Fast payout minimum fee: $0.50'),
    ('platform.community_org_id', 'null', 'UUID of the community fund organization');

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Update updated_at timestamps automatically
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER actors_updated_at BEFORE UPDATE ON actors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER vendors_updated_at BEFORE UPDATE ON vendors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER gift_cards_updated_at BEFORE UPDATE ON gift_cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER gift_card_daily_loads_updated_at BEFORE UPDATE ON gift_card_daily_loads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER mojaloop_participants_updated_at BEFORE UPDATE ON mojaloop_participants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- VIEWS: Useful aggregations
-- ============================================================================

-- Vendor earnings summary
CREATE VIEW vendor_earnings_summary AS
SELECT
    v.id AS vendor_id,
    v.business_name,
    COUNT(DISTINCT gct.id) AS total_transactions,
    COALESCE(SUM(gct.amount_usd), 0) AS total_sales_usd,
    COALESCE(SUM(gct.amount_usd * (1 - v.get_rate)), 0) AS total_earnings_usd,
    COALESCE(SUM(gct.amount_usd * v.get_rate), 0) AS total_get_accrued_usd,
    COALESCE(SUM(CASE WHEN p.status = 'completed' THEN p.net_to_vendor_usd ELSE 0 END), 0) AS total_paid_out_usd
FROM vendors v
LEFT JOIN gift_card_transactions gct ON gct.vendor_id = v.id AND gct.transaction_type = 'redemption'
LEFT JOIN payouts p ON p.vendor_id = v.id
WHERE v.status = 'active'
GROUP BY v.id, v.business_name;

-- Gift card balances
CREATE VIEW gift_card_balances AS
SELECT
    gc.id AS card_id,
    gc.card_token,
    gc.status,
    gc.current_balance_usd,
    gc.original_balance_usd,
    gc.original_balance_usd - gc.current_balance_usd AS total_spent_usd,
    COUNT(gct.id) AS transaction_count,
    MAX(gct.created_at) AS last_transaction_at
FROM gift_cards gc
LEFT JOIN gift_card_transactions gct ON gct.gift_card_id = gc.id
GROUP BY gc.id, gc.card_token, gc.status, gc.current_balance_usd, gc.original_balance_usd;

-- Tax filing schedule
CREATE VIEW tax_filing_schedule AS
SELECT
    v.id AS vendor_id,
    v.business_name,
    v.filing_frequency,
    v.next_filing_date,
    COUNT(tf.id) FILTER (WHERE tf.status = 'filed') AS filings_completed,
    COUNT(tf.id) FILTER (WHERE tf.status = 'failed') AS filings_failed,
    COALESCE(SUM(tf.get_due_usd) FILTER (WHERE tf.status = 'filed'), 0) AS total_get_paid_usd
FROM vendors v
LEFT JOIN tax_filings tf ON tf.vendor_id = v.id
WHERE v.status = 'active'
GROUP BY v.id, v.business_name, v.filing_frequency, v.next_filing_date;
