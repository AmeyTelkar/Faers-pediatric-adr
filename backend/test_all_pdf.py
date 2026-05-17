import sys
import time
from app.database import sync_session_factory
from sqlalchemy import text
from app.routers.pdf_export import build_pdf

db = sync_session_factory()
print("Fetching ALL data...")
start = time.time()
res = db.execute(text("SELECT compute_faers_report(NULL, NULL)")).scalar()
data = dict(res)
print(f"Data fetched in {time.time()-start:.2f}s. Signals: {len(data.get('top_signals', []))}")

print("Building PDF...")
start = time.time()
pdf = build_pdf(data, "ALL", "All Age Groups")
print(f"PDF built in {time.time()-start:.2f}s. Length: {len(pdf)}")
