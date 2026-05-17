from app.database import sync_session_factory
from sqlalchemy import text
from app.core.cache import set_cached_report
import time
import json

db = sync_session_factory()

def warm_cache(quarter, age_group):
    q_label = quarter or "ALL"
    a_label = age_group or "all"
    print(f"Warming cache for {q_label} | {a_label}...")
    t0 = time.time()
    
    result = db.execute(
        text("SELECT compute_faers_report(:q, :a)"),
        {"q": quarter, "a": age_group}
    ).scalar()
    
    data = dict(result)
    set_cached_report(quarter, age_group, data)
    print(f"  -> Done in {time.time()-t0:.2f}s")

if __name__ == "__main__":
    warm_cache(None, None)      # ALL
    warm_cache("2021Q1", None)  # 2021Q1
    warm_cache("2021Q2", None)  # 2021Q2
