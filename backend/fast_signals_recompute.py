import os
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.routers.signals import _recompute_signals

engine = create_engine("postgresql://postgres:Lhd%40800pm@localhost:5432/faers_pediatric")
print("Recomputing signals for 2024Q1...", flush=True)

with Session(engine) as db:
    count = _recompute_signals(db, min_n=3, quarter_filter="2024Q1")
    print(f"Successfully computed {count} signals for 2024Q1!", flush=True)
