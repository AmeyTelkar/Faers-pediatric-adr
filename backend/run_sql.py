import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from app.database import sync_engine
from sqlalchemy import text

with open('stored_proc.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

with sync_engine.begin() as conn:
    print("Creating stored procedure...")
    conn.execute(text(sql))
    
    print("Creating indexes...")
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_signal_cache_is_signal_n11
        ON signal_cache(is_signal, n11, quarter_filter, age_group);
    """))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_demographics_quarter_superseded
        ON demographics(source_quarter, is_superseded, age_group);
    """))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_drugs_rolecod_primaryid
        ON drugs(role_cod, primaryid);
    """))
    print("Done!")
