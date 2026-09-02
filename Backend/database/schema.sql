-- Simple table to store sales leads (same columns as leads.csv).
-- crm_record_hash is UNIQUE so the same person cannot be saved twice
-- by different agents (that is how we stop duplicates).

CREATE TABLE leads (
    id INTEGER PRIMARY KEY,
    lead_id TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    source TEXT NOT NULL,
    city TEXT,
    area TEXT,
    property_type TEXT,
    budget_pkr_lac REAL,
    bedrooms INTEGER,
    first_response_minutes REAL,
    calls_made INTEGER DEFAULT 0,
    total_call_seconds REAL DEFAULT 0,
    whatsapp_replies INTEGER DEFAULT 0,
    site_visits INTEGER DEFAULT 0,
    agent_experience_years REAL,
    is_overseas INTEGER DEFAULT 0,
    referred_by_existing_client INTEGER DEFAULT 0,
    has_financing_approved INTEGER DEFAULT 0,
    token_amount_received_pkr REAL DEFAULT 0,
    crm_record_hash INTEGER UNIQUE NOT NULL,
    converted INTEGER DEFAULT 0
);

-- Speeds up filtering by source and converted.
CREATE INDEX idx_source ON leads (source);
CREATE INDEX idx_converted ON leads (converted);
