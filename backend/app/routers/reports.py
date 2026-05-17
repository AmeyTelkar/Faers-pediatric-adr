from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_sync_db
from app.core.cache import get_cached_report, set_cached_report

router = APIRouter()

@router.get("/summary")
def get_report_summary(
    quarter: str | None = Query(None),
    age_group: str | None = Query(None),
    signal_limit: int = Query(50),
    db: Session = Depends(get_sync_db),
):
    # 1. Try cache first
    cached = get_cached_report(quarter, age_group)
    
    if not cached:
        # 2. Call stored procedure — all computation inside PostgreSQL
        result = db.execute(
            text("SELECT compute_faers_report(:quarter, :age_group)"),
            {"quarter": quarter, "age_group": age_group}
        ).scalar()
        cached = dict(result)
        # 3. Write to cache
        set_cached_report(quarter, age_group, cached)

    # 4. Return summary with limited signals to prevent browser freezing!
    # Make a shallow copy of the dict to avoid mutating the cache
    response_data = dict(cached)
    
    # Slice the signals array for the UI table
    if "top_signals" in response_data and signal_limit > 0:
        response_data["top_signals"] = response_data["top_signals"][:signal_limit]

    return response_data
