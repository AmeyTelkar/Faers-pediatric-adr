"""Pre-compute signal cache and add performance indexes."""
import psycopg2
import time

conn = psycopg2.connect(
    host='localhost', user='postgres', password='Lhd@800pm',
    port=5432, dbname='faers_pediatric'
)
conn.autocommit = True
cur = conn.cursor()

# Add indexes for faster JOINs if they don't exist
indexes = [
    ("idx_drugs_pid", "drugs", "primaryid"),
    ("idx_drugs_role", "drugs", "role_cod"),
    ("idx_drugs_name", "drugs", "drugname_normalized"),
    ("idx_reactions_pid", "reactions", "primaryid"),
    ("idx_reactions_pt", "reactions", "pt_term"),
    ("idx_outcomes_pid", "outcomes", "primaryid"),
    ("idx_demo_age_group", "demographics", "age_group"),
    ("idx_demo_quarter", "demographics", "source_quarter"),
]

for idx_name, table, col in indexes:
    try:
        cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({col})")
        print(f"  Index {idx_name} ensured")
    except Exception as e:
        print(f"  Index {idx_name} skipped: {e}")

print("\nAll indexes created. Now pre-computing signals...")
conn.close()

# Trigger signal computation via API
import requests
print("Calling POST /api/signals/recompute (this may take 1-3 minutes)...")
start = time.time()
try:
    r = requests.post("http://localhost:8000/api/signals/recompute?min_n=3", timeout=600)
    elapsed = time.time() - start
    print(f"  Result: {r.json()}")
    print(f"  Took {elapsed:.1f}s")
except Exception as e:
    print(f"  Error: {e}")
