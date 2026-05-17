import os
from app.database import sync_session_factory
from sqlalchemy import text
from app.routers.reactions import top_pt_terms, soc_heatmap, drug_adr_pairs
import time

db = sync_session_factory()

def warm_cache():
    print("Warming up ADR Analysis Reactions Cache (Disk Persistent)...")
    
    # We only care about the heavy "ALL" quarters query, which times out the frontend.
    print("\n1. Warming up Top PT (All Quarters)...")
    t0 = time.time()
    top_pt_terms(age_group=None, quarter=None, limit=20, db=db)
    print(f"Done in {time.time()-t0:.2f}s")
    
    print("\n2. Warming up SOC Heatmap (All Quarters)...")
    t0 = time.time()
    soc_heatmap(quarter=None, limit=30, db=db)
    print(f"Done in {time.time()-t0:.2f}s")
    
    print("\n3. Warming up Drug-ADR Pairs (All Quarters)...")
    t0 = time.time()
    drug_adr_pairs(age_group=None, quarter=None, min_count=3, limit=50, db=db)
    print(f"Done in {time.time()-t0:.2f}s")
    
    print("\nCache warming complete! The ADR Analysis dashboard will now load instantly.")

if __name__ == "__main__":
    warm_cache()
