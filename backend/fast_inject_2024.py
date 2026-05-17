import os
import time
import pandas as pd
from sqlalchemy import create_engine, text

# 1. Load files
DATA_DIR = r"E:\Adverse drugs Project 2\faers-pediatric-adr\data\2024\faers_ascii_2024q1\ascii"
QUARTER = "2024Q1"
YEAR = 2024

files_to_load = ["DEMO24Q1.txt", "DRUG24Q1.txt", "REAC24Q1.txt", "OUTC24Q1.txt", "RPSR24Q1.txt", "THER24Q1.txt", "INDI24Q1.txt"]
files_bytes = {}

print("Reading files...")
for fn in files_to_load:
    path = os.path.join(DATA_DIR, fn)
    if os.path.exists(path):
        with open(path, "rb") as f:
            # We map to the standard prefixes DEMO, DRUG, REAC etc. for the orchestrator
            # Wait, the pipeline parses the first 4 letters as type.
            files_bytes[fn] = f.read()

from app.pipeline.orchestrator import _run_pipeline_sync

print("Running pipeline locally with SKIP_RXNORM=True...")
preview_stats, demo, parsed = _run_pipeline_sync(files_bytes, QUARTER, skip_rxnorm=True)

print("Connecting to DB...")
engine = create_engine("postgresql://postgres:Lhd%40800pm@localhost:5432/faers_pediatric")

session_id = "test-2024-data"
CHUNK = 20000

print("Inserting DEMO...")
demo["session_id"] = session_id
demo["caseid"] = pd.to_numeric(demo["caseid"], errors="coerce")
demo.to_sql("demographics", engine, if_exists="append", index=False, chunksize=CHUNK, method="multi")

for table_name, df_dict_key in [("drugs", "DRUG"), ("reactions", "REAC"), ("outcomes", "OUTC"), ("report_sources", "RPSR"), ("therapy", "THER"), ("indications", "INDI")]:
    if df_dict_key in parsed:
        print(f"Inserting {table_name}...")
        df = parsed[df_dict_key]
        df["caseid"] = pd.to_numeric(df["caseid"], errors="coerce")
        # Any specific type casting? The main upload.py did a little bit. We'll just push directly.
        df.to_sql(table_name, engine, if_exists="append", index=False, chunksize=CHUNK, method="multi")

print("Done inserting. The data should now appear.")
