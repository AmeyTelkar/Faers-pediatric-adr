import pandas as pd
import sqlalchemy as sa

engine = sa.create_engine('postgresql://postgres:Lhd%40800pm@localhost:5432/faers_pediatric')

tables = ["demographics", "drugs", "reactions", "outcomes", "therapy", "indications", "report_sources"]
print("2024Q1 Row Counts:")
for t in tables:
    query = f"SELECT COUNT(*) as c FROM {t} WHERE source_quarter = '2024Q1'"
    df = pd.read_sql(query, engine)
    print(f"{t}: {df['c'][0]}")
