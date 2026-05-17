import pandas as pd
import sqlalchemy as sa
engine = sa.create_engine('postgresql://postgres:Lhd%40800pm@localhost:5432/faers_pediatric')

res = pd.read_sql("SELECT count(*) FROM loaded_quarters WHERE quarter = '2024Q2'", engine)
count = res.iloc[0,0]

if count == 0:
    print("Fixing loaded_quarters for 2024Q2 by manually inserting it...")
    with engine.begin() as conn:
        conn.execute(sa.text("""
            INSERT INTO loaded_quarters (quarter, year, quarter_num, quarter_label, pediatric_rows, signal_count, gnn_trained)
            VALUES ('2024Q2', 2024, 2, '2024 Q2', 173721, 0, False)
        """))
    print("Fixed! Now computing missing signals...")
else:
    print("loaded_quarters is natively fine! Checking signals next.")
