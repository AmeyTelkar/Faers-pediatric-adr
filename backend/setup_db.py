"""Setup database and run schema creation."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to default postgres database
try:
    conn = psycopg2.connect(
        host="localhost", port=5432,
        user="postgres", password="Lhd@800pm",
        dbname="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Check if database exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname='faers_pediatric'")
    exists = cur.fetchone()

    if not exists:
        cur.execute("CREATE DATABASE faers_pediatric")
        print("[OK] Created database 'faers_pediatric'")
    else:
        print("[OK] Database 'faers_pediatric' already exists")

    cur.close()
    conn.close()

    # Now connect to faers_pediatric and create schema
    conn = psycopg2.connect(
        host="localhost", port=5432,
        user="postgres", password="Lhd@800pm",
        dbname="faers_pediatric"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Create tables
    schema_sql = """
    -- Upload sessions
    CREATE TABLE IF NOT EXISTS upload_sessions (
        session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        quarter VARCHAR(6) NOT NULL,
        year INTEGER NOT NULL,
        files_uploaded TEXT[] NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        row_stats JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Demographics
    CREATE TABLE IF NOT EXISTS demographics (
        primaryid BIGINT PRIMARY KEY,
        caseid BIGINT NOT NULL,
        caseversion INTEGER NOT NULL,
        i_f_code VARCHAR(1),
        event_dt DATE,
        fda_dt DATE,
        rept_cod VARCHAR(10),
        age_raw NUMERIC,
        age_cod VARCHAR(5),
        age_years NUMERIC,
        age_group VARCHAR(20),
        is_age_imputed BOOLEAN DEFAULT FALSE,
        sex VARCHAR(1),
        weight_kg NUMERIC,
        occp_cod VARCHAR(5),
        reporter_country VARCHAR(5),
        occr_country VARCHAR(5),
        event_dt_partial BOOLEAN DEFAULT FALSE,
        source_quarter VARCHAR(6) NOT NULL,
        session_id UUID REFERENCES upload_sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_demo_age_group ON demographics(age_group);
    CREATE INDEX IF NOT EXISTS idx_demo_quarter ON demographics(source_quarter);
    CREATE INDEX IF NOT EXISTS idx_demo_caseid ON demographics(caseid);

    -- Drugs
    CREATE TABLE IF NOT EXISTS drugs (
        id BIGSERIAL PRIMARY KEY,
        primaryid BIGINT NOT NULL REFERENCES demographics(primaryid),
        caseid BIGINT NOT NULL,
        drug_seq INTEGER NOT NULL,
        role_cod VARCHAR(2),
        drugname_original TEXT,
        drugname_normalized TEXT,
        rxcui VARCHAR(20),
        route VARCHAR(50),
        dose_amt VARCHAR(20),
        dose_unit VARCHAR(20),
        dose_form VARCHAR(50),
        dose_freq VARCHAR(20),
        dechal VARCHAR(1),
        rechal VARCHAR(1),
        source_quarter VARCHAR(6) NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_drugs_primaryid ON drugs(primaryid);
    CREATE INDEX IF NOT EXISTS idx_drugs_normalized ON drugs(drugname_normalized);
    CREATE INDEX IF NOT EXISTS idx_drugs_role ON drugs(role_cod);

    -- Reactions
    CREATE TABLE IF NOT EXISTS reactions (
        id BIGSERIAL PRIMARY KEY,
        primaryid BIGINT NOT NULL REFERENCES demographics(primaryid),
        caseid BIGINT NOT NULL,
        pt_term TEXT NOT NULL,
        drug_rec_act TEXT,
        source_quarter VARCHAR(6) NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_reac_primaryid ON reactions(primaryid);
    CREATE INDEX IF NOT EXISTS idx_reac_pt ON reactions(pt_term);

    -- Outcomes
    CREATE TABLE IF NOT EXISTS outcomes (
        id BIGSERIAL PRIMARY KEY,
        primaryid BIGINT NOT NULL REFERENCES demographics(primaryid),
        caseid BIGINT NOT NULL,
        outc_cod VARCHAR(2) NOT NULL,
        severity_score INTEGER NOT NULL,
        source_quarter VARCHAR(6) NOT NULL
    );

    -- Report sources
    CREATE TABLE IF NOT EXISTS report_sources (
        id BIGSERIAL PRIMARY KEY,
        primaryid BIGINT NOT NULL REFERENCES demographics(primaryid),
        caseid BIGINT NOT NULL,
        rpsr_cod VARCHAR(5),
        source_quarter VARCHAR(6) NOT NULL
    );

    -- Therapy
    CREATE TABLE IF NOT EXISTS therapy (
        id BIGSERIAL PRIMARY KEY,
        primaryid BIGINT NOT NULL REFERENCES demographics(primaryid),
        caseid BIGINT NOT NULL,
        dsg_drug_seq INTEGER,
        start_dt DATE,
        end_dt DATE,
        duration_days NUMERIC,
        start_dt_partial BOOLEAN DEFAULT FALSE,
        end_dt_partial BOOLEAN DEFAULT FALSE,
        source_quarter VARCHAR(6) NOT NULL
    );

    -- Indications
    CREATE TABLE IF NOT EXISTS indications (
        id BIGSERIAL PRIMARY KEY,
        primaryid BIGINT NOT NULL REFERENCES demographics(primaryid),
        caseid BIGINT NOT NULL,
        drug_seq INTEGER,
        indi_pt TEXT,
        source_quarter VARCHAR(6) NOT NULL
    );

    -- Drug normalization cache
    CREATE TABLE IF NOT EXISTS drug_norm_cache (
        drugname_original_lower TEXT PRIMARY KEY,
        drugname_normalized TEXT,
        rxcui VARCHAR(20),
        lookup_source VARCHAR(20),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Signal cache
    CREATE TABLE IF NOT EXISTS signal_cache (
        id BIGSERIAL PRIMARY KEY,
        drugname_normalized TEXT NOT NULL,
        pt_term TEXT NOT NULL,
        age_group VARCHAR(20) NOT NULL,
        n11 INTEGER NOT NULL,
        n1x INTEGER NOT NULL,
        nx1 INTEGER NOT NULL,
        nxx INTEGER NOT NULL,
        prr NUMERIC,
        prr_ci_lower NUMERIC,
        prr_chi2 NUMERIC,
        ror NUMERIC,
        ror_ci_lower NUMERIC,
        ror_ci_upper NUMERIC,
        ic NUMERIC,
        ic025 NUMERIC,
        ebgm NUMERIC,
        eb05 NUMERIC,
        computed_at TIMESTAMPTZ DEFAULT NOW(),
        source_quarters TEXT[] NOT NULL,
        UNIQUE(drugname_normalized, pt_term, age_group)
    );
    CREATE INDEX IF NOT EXISTS idx_signal_drug ON signal_cache(drugname_normalized);
    CREATE INDEX IF NOT EXISTS idx_signal_adr ON signal_cache(pt_term);
    CREATE INDEX IF NOT EXISTS idx_signal_age_group ON signal_cache(age_group);
    """

    cur.execute(schema_sql)
    print("[OK] All tables and indexes created successfully")

    # Verify
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    tables = [r[0] for r in cur.fetchall()]
    print(f"[OK] Tables in database: {tables}")

    cur.close()
    conn.close()
    print("\n[OK] Database setup complete!")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

