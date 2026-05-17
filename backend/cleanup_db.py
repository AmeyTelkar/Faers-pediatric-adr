"""Force cleanup: terminate idle connections and clear data."""
import psycopg2
import sys

try:
    # Connect to postgres DB to terminate locks
    conn = psycopg2.connect(
        host="localhost", port=5432,
        user="postgres", password="Lhd@800pm",
        dbname="postgres"
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Terminate all other connections to faers_pediatric
    cur.execute("""
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = 'faers_pediatric' 
        AND pid <> pg_backend_pid()
    """)
    terminated = cur.fetchall()
    print(f"Terminated {len(terminated)} stale connections")
    cur.close()
    conn.close()
    
    # Now connect and clean
    conn = psycopg2.connect(
        host="localhost", port=5432,
        user="postgres", password="Lhd@800pm",
        dbname="faers_pediatric"
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Check schema
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'upload_sessions' 
        ORDER BY ordinal_position
    """)
    print("\nupload_sessions columns:")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}({r[2]})")
    
    # Truncate all tables (faster than DELETE for large tables)
    tables = ['signal_cache', 'indications', 'therapy', 'report_sources', 
              'outcomes', 'reactions', 'drugs', 'demographics', 'upload_sessions']
    for t in tables:
        try:
            cur.execute(f"TRUNCATE TABLE {t} CASCADE")
            print(f"  Truncated {t}")
        except Exception as e:
            print(f"  Skip {t}: {e}")
    
    print("\n[OK] Database cleaned!")
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
