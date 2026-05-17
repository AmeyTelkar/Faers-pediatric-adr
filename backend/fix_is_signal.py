import sqlalchemy as sa

engine = sa.create_engine('postgresql://postgres:Lhd%40800pm@localhost:5432/faers_pediatric')

with engine.begin() as conn:
    conn.execute(sa.text("""
        UPDATE signal_cache 
        SET is_signal = TRUE
        WHERE (prr >= 2 AND prr_chi2 >= 4)
           OR (ror >= 2 AND ror_ci_lower > 1)
           OR (ic025 > 0)
           OR (eb05 > 2)
    """))
    print("Updated is_signal flag in database.")
