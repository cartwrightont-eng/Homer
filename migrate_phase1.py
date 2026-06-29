"""
Phase 1 migration — run this ONCE against your Neon database.
It extends the existing schema with all new tables.
Safe to run repeatedly (uses IF NOT EXISTS and ALTER TABLE IF NOT EXISTS).

Run:  python3 migrate_phase1.py
"""

from database import db_cursor

MIGRATIONS = [

# ── 1. Extend users table ──────────────────────────────────────────────────
"""
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS phone          VARCHAR(20),
  ADD COLUMN IF NOT EXISTS profile_photo_url TEXT,
  ADD COLUMN IF NOT EXISTS bio            TEXT,
  ADD COLUMN IF NOT EXISTS review_score   NUMERIC(3,2) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS wallet_balance NUMERIC(12,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS is_verified    BOOLEAN DEFAULT FALSE;
""",

# ── 2. Extend accommodations table ────────────────────────────────────────
"""
ALTER TABLE accommodations
  ADD COLUMN IF NOT EXISTS latitude       NUMERIC(10,7),
  ADD COLUMN IF NOT EXISTS longitude      NUMERIC(10,7),
  ADD COLUMN IF NOT EXISTS listing_type   VARCHAR(20) DEFAULT 'rent',
  ADD COLUMN IF NOT EXISTS property_type  VARCHAR(30) DEFAULT 'apartment',
  ADD COLUMN IF NOT EXISTS size_sqft      INTEGER,
  ADD COLUMN IF NOT EXISTS virtual_tour_url TEXT,
  ADD COLUMN IF NOT EXISTS amenities_text TEXT;
""",

# ── 3. Accommodation photos ────────────────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS accommodation_photos (
  id               SERIAL PRIMARY KEY,
  accommodation_id INTEGER NOT NULL REFERENCES accommodations(id) ON DELETE CASCADE,
  url              TEXT NOT NULL,
  caption          TEXT,
  sort_order       INTEGER DEFAULT 0,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
""",

# ── 4. Favourites ──────────────────────────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS favourites (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  accommodation_id INTEGER NOT NULL REFERENCES accommodations(id) ON DELETE CASCADE,
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_id, accommodation_id)
);
""",

# ── 5. Tenant applications / pipeline ─────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS tenant_applications (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  accommodation_id INTEGER NOT NULL REFERENCES accommodations(id) ON DELETE CASCADE,
  message          TEXT,
  status           VARCHAR(20) DEFAULT 'pending',
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at       TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_id, accommodation_id)
);
""",

# ── 6. Payments ────────────────────────────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS payments (
  id               SERIAL PRIMARY KEY,
  payer_id         INTEGER NOT NULL REFERENCES users(id),
  accommodation_id INTEGER REFERENCES accommodations(id),
  amount           NUMERIC(12,2) NOT NULL,
  surcharge        NUMERIC(12,2) DEFAULT 0,
  total_amount     NUMERIC(12,2) NOT NULL,
  payment_type     VARCHAR(20) NOT NULL,
  status           VARCHAR(20) DEFAULT 'pending',
  reference        VARCHAR(100),
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
""",

# ── 7. Landlord wallet transactions ───────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS wallet_transactions (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount           NUMERIC(12,2) NOT NULL,
  transaction_type VARCHAR(20) NOT NULL,
  description      TEXT,
  reference_id     INTEGER,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
""",

# ── 8. Reviews ─────────────────────────────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS reviews (
  id            SERIAL PRIMARY KEY,
  reviewer_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  target_id     INTEGER NOT NULL,
  target_type   VARCHAR(30) NOT NULL,
  rating        NUMERIC(2,1) NOT NULL CHECK (rating >= 1 AND rating <= 5),
  comment       TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (reviewer_id, target_id, target_type)
);
""",

# ── 9. Chat ────────────────────────────────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS conversations (
  id               SERIAL PRIMARY KEY,
  tenant_id        INTEGER NOT NULL REFERENCES users(id),
  landlord_id      INTEGER NOT NULL REFERENCES users(id),
  accommodation_id INTEGER NOT NULL REFERENCES accommodations(id),
  last_message     TEXT,
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at       TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (tenant_id, landlord_id, accommodation_id)
);
""",

"""
CREATE TABLE IF NOT EXISTS messages (
  id              SERIAL PRIMARY KEY,
  conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  sender_id       INTEGER NOT NULL REFERENCES users(id),
  content         TEXT NOT NULL,
  is_read         BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
""",

# ── 10. Tour bookings ─────────────────────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS tour_bookings (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL REFERENCES users(id),
  accommodation_id INTEGER NOT NULL REFERENCES accommodations(id),
  tour_type        VARCHAR(20) NOT NULL,
  scheduled_at     TIMESTAMPTZ,
  status           VARCHAR(20) DEFAULT 'pending',
  notes            TEXT,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
""",

# ── 11. Verification documents ────────────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS verification_documents (
  id                SERIAL PRIMARY KEY,
  user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  doc_type          VARCHAR(40) NOT NULL,
  file_url          TEXT NOT NULL,
  accommodation_id  INTEGER REFERENCES accommodations(id),
  status            VARCHAR(20) DEFAULT 'pending',
  rejection_reason  TEXT,
  reviewed_at       TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);
""",

# ── 12. Service providers ─────────────────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS service_providers (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  business_name    VARCHAR(100),
  category         VARCHAR(50) NOT NULL,
  description      TEXT,
  base_price       NUMERIC(10,2),
  price_unit       VARCHAR(20) DEFAULT 'per_job',
  coverage_area    TEXT,
  is_verified      BOOLEAN DEFAULT FALSE,
  is_online        BOOLEAN DEFAULT FALSE,
  avg_rating       NUMERIC(3,2) DEFAULT NULL,
  current_lat      NUMERIC(10,7),
  current_lng      NUMERIC(10,7),
  location_updated_at TIMESTAMPTZ,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
""",

# ── 13. HomerrFix jobs ────────────────────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS fix_jobs (
  id               SERIAL PRIMARY KEY,
  tenant_id        INTEGER NOT NULL REFERENCES users(id),
  provider_id      INTEGER NOT NULL REFERENCES service_providers(id),
  category         VARCHAR(50),
  description      TEXT,
  address          TEXT,
  lat              NUMERIC(10,7),
  lng              NUMERIC(10,7),
  status           VARCHAR(30) DEFAULT 'pending',
  quoted_price     NUMERIC(10,2),
  final_price      NUMERIC(10,2),
  notes            TEXT,
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at       TIMESTAMPTZ DEFAULT NOW()
);
""",

# ── 14. Insurance policies ────────────────────────────────────────────────
"""
CREATE TABLE IF NOT EXISTS insurance_policies (
  id             SERIAL PRIMARY KEY,
  user_id        INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  tier           VARCHAR(20) NOT NULL,
  monthly_fee    NUMERIC(10,2) NOT NULL,
  coverage_type  VARCHAR(20) NOT NULL,
  coverage_value NUMERIC(10,2) NOT NULL,
  status         VARCHAR(20) DEFAULT 'active',
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  updated_at     TIMESTAMPTZ DEFAULT NOW()
);
""",

# ── 15. Indexes for performance ───────────────────────────────────────────
"""
CREATE INDEX IF NOT EXISTS idx_accommodations_landlord ON accommodations(landlord_id);
CREATE INDEX IF NOT EXISTS idx_accommodations_status   ON accommodations(status);
CREATE INDEX IF NOT EXISTS idx_messages_conversation   ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_tenant         ON fix_jobs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_provider       ON fix_jobs(provider_id);
CREATE INDEX IF NOT EXISTS idx_reviews_target          ON reviews(target_id, target_type);
CREATE INDEX IF NOT EXISTS idx_wallet_user             ON wallet_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_payer          ON payments(payer_id);
""",
]


def run():
    print("Running Phase 1 migration...\n")
    with db_cursor(commit=True) as (conn, cur):
        for i, sql in enumerate(MIGRATIONS, 1):
            try:
                cur.execute(sql)
                label = sql.strip().split("\n")[0][:60]
                print(f"  ✅ [{i:02d}] {label}")
            except Exception as e:
                print(f"  ⚠️  [{i:02d}] Skipped or partial: {e}")
    print("\n✅ Phase 1 migration complete.")


if __name__ == "__main__":
    run()
