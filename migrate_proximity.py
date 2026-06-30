"""
Phase 2c migration:
1. Adds is_online to service_providers (must be true for proximity matching)
2. Adds lat/lng to fix_jobs if missing (needed for distance/ETA calc)
3. Backfills any existing 'accepted' jobs where provider_id was wrongly
   set to a user_id instead of service_providers.id (bug fix)

Run:  python3 migrate_proximity.py
"""
from database import db_cursor

MIGRATIONS = [
    """
    ALTER TABLE service_providers
      ADD COLUMN IF NOT EXISTS is_online BOOLEAN DEFAULT FALSE;
    """,
    """
    ALTER TABLE service_providers
      ADD COLUMN IF NOT EXISTS base_price NUMERIC(10,2);
    """,
    """
    ALTER TABLE fix_jobs
      ADD COLUMN IF NOT EXISTS lat NUMERIC(10,7);
    """,
    """
    ALTER TABLE fix_jobs
      ADD COLUMN IF NOT EXISTS lng NUMERIC(10,7);
    """,
]

def run():
    print("Running proximity migration...\n")
    with db_cursor(commit=True) as (conn, cur):
        for i, sql in enumerate(MIGRATIONS, 1):
            try:
                cur.execute(sql)
                label = sql.strip().split("\n")[0][:60]
                print(f"  ✅ [{i}] {label}")
            except Exception as e:
                print(f"  ⚠️  [{i}] {e}")

    print("\nChecking for the provider_id bug (user_id stored instead of service_providers.id)...")
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            SELECT j.id, j.provider_id
            FROM fix_jobs j
            WHERE j.provider_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM service_providers sp WHERE sp.id = j.provider_id
              )
        """)
        broken = cur.fetchall()
        if not broken:
            print("  ✅ No broken provider_id references found.")
        else:
            print(f"  ⚠️  Found {len(broken)} job(s) with provider_id pointing to a user_id instead of service_providers.id")
            fixed = 0
            for row in broken:
                job_id = row['id']
                bad_id = row['provider_id']
                cur.execute("SELECT id FROM service_providers WHERE user_id=%s", (bad_id,))
                sp = cur.fetchone()
                if sp:
                    cur.execute("UPDATE fix_jobs SET provider_id=%s WHERE id=%s", (sp['id'], job_id))
                    fixed += 1
            print(f"  ✅ Repaired {fixed} job(s)")

    print("\nDone.")

if __name__ == "__main__":
    run()
