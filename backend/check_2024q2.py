import pandas as pd
import sqlalchemy as sa
engine = sa.create_engine('postgresql://postgres:Lhd%40800pm@localhost:5432/faers_pediatric')
tabs = ["demographics", "drugs", "reactions", "outcomes", "therapy", "indications", "report_sources"]
for t in tabs:
    df = pd.read_sql(f"SELECT count(*) FROM {t} WHERE source_quarter = '2024Q2'", engine)
    print(t, df.iloc[0,0])
