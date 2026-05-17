import sys
from app.database import sync_session_factory
from sqlalchemy import text
from app.routers.pdf_export import build_pdf

db = sync_session_factory()
try:
    print("Executing query...")
    res = db.execute(
        text("SELECT compute_faers_report(:q, NULL)"),
        {"q": "2025Q4"}
    ).scalar()
    
    if not res:
        print("No result")
        sys.exit(1)
        
    data = dict(res)
    print("Building PDF...")
    pdf_bytes = build_pdf(data, "2025Q4", "All Age Groups")
    print(f"PDF generated: {len(pdf_bytes)} bytes")
    
except Exception as e:
    import traceback
    traceback.print_exc()
