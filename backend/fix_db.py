"""Fix: stamp alembic version and create missing gnn_checkpoints table."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', user='postgres', password='Lhd@800pm',
    port=5432, dbname='faers_pediatric'
)
conn.autocommit = True
cur = conn.cursor()

# Create alembic_version table and stamp as 002
cur.execute("""
    CREATE TABLE IF NOT EXISTS alembic_version (
        version_num VARCHAR(32) NOT NULL,
        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
    )
""")
cur.execute("DELETE FROM alembic_version")
cur.execute("INSERT INTO alembic_version (version_num) VALUES ('002')")
print("Alembic version stamped to 002")

# Create gnn_checkpoints if missing
cur.execute("""
    CREATE TABLE IF NOT EXISTS gnn_checkpoints (
        id BIGSERIAL PRIMARY KEY,
        age_group VARCHAR(15) NOT NULL,
        val_auc NUMERIC,
        test_auc NUMERIC,
        epochs INTEGER,
        n_drugs INTEGER,
        n_adrs INTEGER,
        n_edges INTEGER,
        checkpoint_path TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    )
""")
print("gnn_checkpoints table ensured")

# Add missing columns to signal_cache (from 002 migration)
for col in ['n10', 'n01', 'n00']:
    try:
        cur.execute(f"ALTER TABLE signal_cache ADD COLUMN {col} INTEGER")
        print(f"  Added {col} to signal_cache")
    except Exception:
        conn.rollback()
        conn.autocommit = True

try:
    cur.execute("ALTER TABLE signal_cache ADD COLUMN is_signal BOOLEAN DEFAULT false")
    print("  Added is_signal to signal_cache")
except Exception:
    conn.rollback()
    conn.autocommit = True

print("Done! Database is ready.")
conn.close()
