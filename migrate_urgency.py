"""
Phase 2b migration — adds urgency priority + notification tracking to fix_jobs.
Safe to re-run.

Run:  python3 migrate_urgency.py
"""
from database import db_cursor

MIGRATIONS = [
    """
    ALTER TABLE fix_jobs
      ADD COLUMN IF NOT EXISTS urgency VARCHAR(20) DEFAULT 'normal';
    """,
    """
    ALTER TABLE fix_jobs
      ADD COLUMN IF NOT EXISTS seen_by_provider BOOLEAN DEFAULT FALSE;
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fix_jobs_urgency ON fix_jobs(urgency);
    """,
]

def run():
    print("Running urgency + notification migration...\n")
    with db_cursor(commit=True) as (conn, cur):
        for i, sql in enumerate(MIGRATIONS, 1):
            try:
                cur.execute(sql)
                label = sql.strip().split("\n")[0][:60]
                print(f"  ✅ [{i}] {label}")
            except Exception as e:
                print(f"  ⚠️  [{i}] {e}")
    print("\nDone.")

if __name__ == "__main__":
    run()
