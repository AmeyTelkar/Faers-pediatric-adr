import os
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import sys
sys.path.append('E:\\Adverse drugs Project 2\\faers-pediatric-adr\\backend')
from app.routers.signals import _recompute_signals
import requests

engine = create_engine("postgresql://postgres:Lhd%40800pm@localhost:5432/faers_pediatric")
print("Recomputing signals for 2024Q2...", flush=True)

with Session(engine) as db:
    count = _recompute_signals(db, min_n=3, quarter_filter="2024Q2")
    print(f"Successfully computed {count} signals for 2024Q2!", flush=True)

print("Fixing is_signal...", flush=True)
with engine.begin() as conn:
    conn.execute(sa.text("""
        UPDATE signal_cache 
        SET is_signal = TRUE
        WHERE quarter_filter = '2024Q2' AND (
           (prr >= 2 AND prr_chi2 >= 4)
           OR (ror >= 2 AND ror_ci_lower > 1)
           OR (ic025 > 0)
           OR (eb05 > 2)
        )
    """))

print("Training GNN for 2024Q2...", flush=True)
try:
    res = requests.post("http://localhost:8000/api/gnn/train/ALL?quarter=2024Q2").json()
    print("GNN Training finished!", res, flush=True)
except Exception as e:
    print("GNN failed:", e)
