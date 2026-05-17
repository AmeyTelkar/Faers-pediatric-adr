import os
from app.database import sync_session_factory
from sqlalchemy import text
from app.routers.pdf_export import build_pdf
from app.core.cache import get_cached_report, set_cached_report
import time

db = sync_session_factory()

OUTPUT_DIR = r"E:\Adverse drugs Project 2\FAERS_Reports_2021_2025"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print(f"Saving all PDF reports to: {OUTPUT_DIR}\n")

# Get list of loaded quarters
quarters = db.execute(text("SELECT DISTINCT source_quarter FROM demographics WHERE is_superseded = FALSE ORDER BY source_quarter")).fetchall()
quarters = [q[0] for q in quarters]

if not quarters:
    print("No quarters found in the database.")
    exit()

def export_quarter(q_val):
    print(f"Generating Report for {q_val or 'ALL QUARTERS'}...")
    t0 = time.time()
    
    # 1. Fetch data
    data = get_cached_report(q_val, None)
    if not data:
        print("  - Cache miss, computing from database...")
        result = db.execute(
            text("SELECT compute_faers_report(:q, :a)"),
            {"q": q_val, "a": None}
        ).scalar()
        data = dict(result)
        set_cached_report(q_val, None, data)
    
    # 2. Build PDF
    print("  - Building PDF...")
    pdf_bytes = build_pdf(data, q_val, "All Age Groups")
    
    # 3. Save to file
    filename = f"FAERS_Pediatric_Report_{q_val or 'ALL'}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)
        
    print(f"  -> Saved {filename} ({len(pdf_bytes)/1024:.1f} KB) in {time.time()-t0:.2f}s\n")

# Generate specific quarters
for q in quarters:
    export_quarter(q)

# Generate ALL quarters consolidated report
export_quarter(None)

print(f"Successfully generated {len(quarters) + 1} reports in {OUTPUT_DIR}!")
