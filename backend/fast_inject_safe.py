import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
import traceback
import sys

DATA_DIR = r"E:\Adverse drugs Project 2\faers-pediatric-adr\data\2024\faers_ascii_2024q1\ascii"
QUARTER = "2024Q1"

files_to_load = ["DEMO24Q1.txt", "DRUG24Q1.txt", "REAC24Q1.txt", "OUTC24Q1.txt", "RPSR24Q1.txt", "THER24Q1.txt", "INDI24Q1.txt"]
files_bytes = {}

print("Reading files...", flush=True)
for fn in files_to_load:
    path = os.path.join(DATA_DIR, fn)
    if os.path.exists(path):
        with open(path, "rb") as f:
            files_bytes[fn] = f.read()

from app.pipeline.orchestrator import _run_pipeline_sync

print("Running pipeline locally with SKIP_RXNORM=True...", flush=True)
try:
    preview_stats, demo, parsed = _run_pipeline_sync(files_bytes, QUARTER, skip_rxnorm=True)
except Exception as e:
    print("Pipeline failed!")
    traceback.print_exc()
    sys.exit(1)

print("Connecting to DB...", flush=True)
engine = create_engine("postgresql://postgres:Lhd%40800pm@localhost:5432/faers_pediatric")
session_id = "test-2024-data"
CHUNK = 20000

# Clear existing 2024Q1 so we don't duplicate
with engine.begin() as conn:
    conn.execute(text("DELETE FROM drugs WHERE source_quarter = '2024Q1'"))
    conn.execute(text("DELETE FROM reactions WHERE source_quarter = '2024Q1'"))
    conn.execute(text("DELETE FROM outcomes WHERE source_quarter = '2024Q1'"))
    conn.execute(text("DELETE FROM report_sources WHERE source_quarter = '2024Q1'"))
    conn.execute(text("DELETE FROM therapy WHERE source_quarter = '2024Q1'"))
    conn.execute(text("DELETE FROM indications WHERE source_quarter = '2024Q1'"))
    conn.execute(text("DELETE FROM demographics WHERE source_quarter = '2024Q1'"))
    print("Cleared existing 2024Q1 data.", flush=True)

try:
    print("Inserting DEMO...", flush=True)
    demo["session_id"] = session_id
    demo["caseid"] = pd.to_numeric(demo["caseid"], errors="coerce")
    demo.to_sql("demographics", engine, if_exists="append", index=False, chunksize=CHUNK, method="multi")
    print("DEMO inserted.", flush=True)

    for table_name, df_dict_key in [("drugs", "DRUG"), ("reactions", "REAC"), ("outcomes", "OUTC"), ("report_sources", "RPSR"), ("therapy", "THER"), ("indications", "INDI")]:
        if df_dict_key in parsed:
            print(f"Inserting {table_name}...", flush=True)
            df = parsed[df_dict_key]
            
            # Ensure caseid numeric
            if "caseid" in df.columns:
                df["caseid"] = pd.to_numeric(df["caseid"], errors="coerce")

            # Remove 'pt' column if 'pt_term' exists (some rename issues)
            if df_dict_key == "REAC" and "pt" in df.columns and "pt_term" in df.columns:
                df.drop(columns=["pt"], inplace=True)
            if df_dict_key == "DRUG" and "drugname" in df.columns and "drugname_original" in df.columns:
                df.drop(columns=["drugname"], inplace=True)
            
            # Remove any columns not in db schema
            try:
                df.to_sql(table_name, engine, if_exists="append", index=False, chunksize=CHUNK, method="multi")
                print(f"{table_name} inserted successfully.", flush=True)
            except Exception as e:
                print(f"Failed to insert {table_name}: {e}", flush=True)

    print("Done inserting. The data should now appear.", flush=True)
except Exception as e:
    print("DB Insert Failed!!")
    traceback.print_exc()
