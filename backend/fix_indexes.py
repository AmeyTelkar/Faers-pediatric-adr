"""Add critical composite indexes and check data types."""
import psycopg2
import time

conn = psycopg2.connect(
    host="localhost", port=5432,
    user="postgres", password="Lhd@800pm",
    dbname="faers_pediatric"
)
conn.autocommit = True
cur = conn.cursor()

# Check primaryid data type
cur.execute("""
    SELECT table_name, column_name, data_type 
    FROM information_schema.columns 
    WHERE column_name = 'primaryid' 
    AND table_schema = 'public'
    ORDER BY table_name
""")
print("primaryid data types:")
for r in cur.fetchall():
    print(f"  {r[0]}.{r[1]}: {r[2]}")

# The JOIN is slow because primaryid might be different types
# Let's check if we need to cast and add proper indexes
print("\nAdding critical indexes...")
t0 = time.perf_counter()

indexes = [
    # CRITICAL: composite indexes for JOIN queries
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_demo_pid_age ON demographics (primaryid, age_group)",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_drugs_pid_drugname ON drugs (primaryid, drugname_normalized)",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reac_pid_pt ON reactions (primaryid, pt_term)",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_outc_pid_cod ON outcomes (primaryid, outc_cod)",
    # Age years index for stats
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_demo_age_years ON demographics (age_years) WHERE age_years IS NOT NULL",
]

for sql in indexes:
    name = sql.split("idx_")[1].split(" ON")[0]
    try:
        cur.execute(sql)
        print(f"  [OK] idx_{name}")
    except Exception as e:
        print(f"  [SKIP] idx_{name}: {e}")

print(f"\nIndexes created in {time.perf_counter()-t0:.1f}s")

# Test the slow query
print("\nTesting JOIN query speed...")
t0 = time.perf_counter()
cur.execute("""
    SELECT r.pt_term, COUNT(*) as count
    FROM reactions r
    JOIN demographics d ON r.primaryid = d.primaryid
    WHERE r.pt_term IS NOT NULL
    GROUP BY r.pt_term ORDER BY count DESC LIMIT 10
""")
results = cur.fetchall()
elapsed = time.perf_counter() - t0
print(f"Top 10 ADRs ({elapsed:.1f}s):")
for r in results:
    print(f"  {r[0]}: {r[1]:,}")

cur.close()
conn.close()
