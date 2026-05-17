"""Fix VARCHAR column sizes to handle real FAERS data."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    conn = psycopg2.connect(
        host="localhost", port=5432,
        user="postgres", password="Lhd@800pm",
        dbname="faers_pediatric"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Widen all VARCHAR columns that may be too small for real FAERS data
    alter_sql = """
    -- Demographics table
    ALTER TABLE demographics ALTER COLUMN i_f_code TYPE VARCHAR(10);
    ALTER TABLE demographics ALTER COLUMN rept_cod TYPE VARCHAR(50);
    ALTER TABLE demographics ALTER COLUMN age_cod TYPE VARCHAR(20);
    ALTER TABLE demographics ALTER COLUMN age_group TYPE VARCHAR(30);
    ALTER TABLE demographics ALTER COLUMN sex TYPE VARCHAR(10);
    ALTER TABLE demographics ALTER COLUMN occp_cod TYPE VARCHAR(20);
    ALTER TABLE demographics ALTER COLUMN reporter_country TYPE VARCHAR(50);
    ALTER TABLE demographics ALTER COLUMN occr_country TYPE VARCHAR(50);
    ALTER TABLE demographics ALTER COLUMN source_quarter TYPE VARCHAR(20);

    -- Drugs table
    ALTER TABLE drugs ALTER COLUMN role_cod TYPE VARCHAR(10);
    ALTER TABLE drugs ALTER COLUMN rxcui TYPE VARCHAR(50);
    ALTER TABLE drugs ALTER COLUMN route TYPE VARCHAR(100);
    ALTER TABLE drugs ALTER COLUMN dose_amt TYPE VARCHAR(100);
    ALTER TABLE drugs ALTER COLUMN dose_unit TYPE VARCHAR(50);
    ALTER TABLE drugs ALTER COLUMN dose_form TYPE VARCHAR(100);
    ALTER TABLE drugs ALTER COLUMN dose_freq TYPE VARCHAR(50);
    ALTER TABLE drugs ALTER COLUMN dechal TYPE VARCHAR(10);
    ALTER TABLE drugs ALTER COLUMN rechal TYPE VARCHAR(10);
    ALTER TABLE drugs ALTER COLUMN source_quarter TYPE VARCHAR(20);

    -- Outcomes table
    ALTER TABLE outcomes ALTER COLUMN outc_cod TYPE VARCHAR(10);
    ALTER TABLE outcomes ALTER COLUMN source_quarter TYPE VARCHAR(20);

    -- Report sources table
    ALTER TABLE report_sources ALTER COLUMN rpsr_cod TYPE VARCHAR(20);
    ALTER TABLE report_sources ALTER COLUMN source_quarter TYPE VARCHAR(20);

    -- Therapy table
    ALTER TABLE therapy ALTER COLUMN source_quarter TYPE VARCHAR(20);

    -- Indications table
    ALTER TABLE indications ALTER COLUMN source_quarter TYPE VARCHAR(20);

    -- Reactions table
    ALTER TABLE reactions ALTER COLUMN source_quarter TYPE VARCHAR(20);

    -- Signal cache
    ALTER TABLE signal_cache ALTER COLUMN age_group TYPE VARCHAR(30);
    """

    cur.execute(alter_sql)
    print("[OK] All column sizes updated successfully")

    # Also clear any partial data from failed insert
    cur.execute("DELETE FROM indications")
    cur.execute("DELETE FROM therapy")
    cur.execute("DELETE FROM report_sources")
    cur.execute("DELETE FROM outcomes")
    cur.execute("DELETE FROM reactions")
    cur.execute("DELETE FROM drugs")
    cur.execute("DELETE FROM demographics")
    cur.execute("DELETE FROM upload_sessions")
    print("[OK] Cleared any partial data from failed inserts")

    cur.close()
    conn.close()
    print("[OK] Schema fix complete! Re-upload and approve data now.")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
