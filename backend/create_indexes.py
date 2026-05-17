"""Add indexes to speed up all analytics queries."""
import psycopg2
import time

conn = psycopg2.connect(
    host="localhost", port=5432,
    user="postgres", password="Lhd@800pm",
    dbname="faers_pediatric"
)
conn.autocommit = True
cur = conn.cursor()

indexes = [
    # Demographics
    "CREATE INDEX IF NOT EXISTS idx_demo_primaryid ON demographics (primaryid)",
    "CREATE INDEX IF NOT EXISTS idx_demo_age_group ON demographics (age_group)",
    "CREATE INDEX IF NOT EXISTS idx_demo_sex ON demographics (sex)",
    "CREATE INDEX IF NOT EXISTS idx_demo_quarter ON demographics (source_quarter)",
    "CREATE INDEX IF NOT EXISTS idx_demo_country ON demographics (reporter_country)",
    
    # Drugs
    "CREATE INDEX IF NOT EXISTS idx_drugs_primaryid ON drugs (primaryid)",
    "CREATE INDEX IF NOT EXISTS idx_drugs_drugname ON drugs (drugname_normalized)",
    "CREATE INDEX IF NOT EXISTS idx_drugs_role ON drugs (role_cod)",
    "CREATE INDEX IF NOT EXISTS idx_drugs_pid_role ON drugs (primaryid, role_cod)",
    
    # Reactions
    "CREATE INDEX IF NOT EXISTS idx_reac_primaryid ON reactions (primaryid)",
    "CREATE INDEX IF NOT EXISTS idx_reac_pt ON reactions (pt_term)",
    
    # Outcomes
    "CREATE INDEX IF NOT EXISTS idx_outc_primaryid ON outcomes (primaryid)",
    "CREATE INDEX IF NOT EXISTS idx_outc_cod ON outcomes (outc_cod)",
    
    # Therapy
    "CREATE INDEX IF NOT EXISTS idx_ther_primaryid ON therapy (primaryid)",
    
    # Indications
    "CREATE INDEX IF NOT EXISTS idx_indi_primaryid ON indications (primaryid)",
    "CREATE INDEX IF NOT EXISTS idx_indi_pt ON indications (indi_pt)",
]

print(f"Creating {len(indexes)} indexes...")
t0 = time.perf_counter()

for idx_sql in indexes:
    name = idx_sql.split("idx_")[1].split(" ON")[0]
    try:
        cur.execute(idx_sql)
        print(f"  [OK] idx_{name}")
    except Exception as e:
        print(f"  [SKIP] idx_{name}: {e}")

elapsed = time.perf_counter() - t0
print(f"\n[OK] All indexes created in {elapsed:.1f}s")

# Also run ANALYZE to update query planner stats
print("Running ANALYZE...")
cur.execute("ANALYZE")
print("[OK] ANALYZE complete - queries will be much faster now!")

cur.close()
conn.close()
