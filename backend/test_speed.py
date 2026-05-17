import sys
import time
import json
from app.database import sync_session_factory
from sqlalchemy import text

db = sync_session_factory()
try:
    print("Executing query for 2025Q4...")
    start = time.time()
    res = db.execute(
        text("SELECT compute_faers_report(:q, NULL)"),
        {"q": "2025Q4"}
    ).scalar()
    
    if not res:
        print("No result")
        sys.exit(1)
        
    print(f"Done in {time.time()-start:.2f} seconds")
    data = dict(res)
    print(f"JSON Length: {len(json.dumps(data))}")
    print(f"Num signals: {len(data.get('top_signals', []))}")
    
except Exception as e:
    import traceback
    traceback.print_exc()
