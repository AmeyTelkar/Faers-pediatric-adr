"""
Demographics Router — age pyramid, country distribution, summary stats.
Uses SYNC database session for fast JOIN queries.
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_sync_db
from app.routers.utils import build_quarter_filter

router = APIRouter()


def _build_where(quarter: Optional[str], extra: dict = None, prefix: str = ""):
    """Build WHERE clause with is_superseded and optional quarter filter."""
    clauses = ["is_superseded = FALSE"]
    
    q_filter, params = build_quarter_filter(quarter, prefix)
    if q_filter:
        # q_filter typically looks like "AND source_quarter = :quarter"
        # We strip the leading "AND " since we're joining with " AND "
        clauses.append(q_filter[4:])
    
    if extra:
        for k, v in extra.items():
            clauses.append(k)
            params.update(v)
    return " AND ".join(clauses), params


@router.get("/quarters")
def get_loaded_quarters(db: Session = Depends(get_sync_db)):
    """Return list of loaded quarters for the frontend dropdown."""
    result = db.execute(text("""
        SELECT quarter, quarter_label, pediatric_rows, loaded_at,
               signal_count, gnn_trained, superseded_rows
        FROM loaded_quarters
        ORDER BY year DESC, quarter_num DESC
    """))
    quarters = result.fetchall()
    return {
        "quarters": [
            {
                "value": q[0],
                "label": q[1],
                "patients": q[2],
                "loaded_at": str(q[3]) if q[3] else None,
                "signals": q[4],
                "gnn_trained": q[5],
                "superseded": q[6],
            }
            for q in quarters
        ],
        "total_quarters": len(quarters),
    }


@router.get("/years")
def get_loaded_years(db: Session = Depends(get_sync_db)):
    result = db.execute(text("""
        SELECT year,
               array_agg(quarter ORDER BY quarter_num) AS quarters,
               SUM(pediatric_rows) AS total_patients,
               SUM(signal_count) AS total_signals,
               COUNT(*) AS quarter_count
        FROM loaded_quarters
        GROUP BY year
        ORDER BY year DESC
    """))
    rows = result.fetchall()
    return {
        "years": [
            {
                "year": r[0],
                "label": str(r[0]),
                "quarters": r[1],
                "total_patients": int(r[2] or 0),
                "total_signals": int(r[3] or 0),
                "quarter_count": r[4]
            }
            for r in rows
        ]
    }


@router.get("/age-pyramid")
def age_pyramid(
    quarter: Optional[str] = Query(None),
    db: Session = Depends(get_sync_db),
):
    """Return age_group x sex counts for building an age pyramid chart."""
    query = """
        SELECT age_group, sex, COUNT(*) as count
        FROM demographics
        WHERE is_superseded = FALSE AND age_group IS NOT NULL
    """
    
    q_filter, params = build_quarter_filter(quarter)
    query += " " + q_filter + " GROUP BY age_group, sex ORDER BY age_group, sex"

    result = db.execute(text(query), params)
    rows = result.fetchall()
    return [{"age_group": r[0], "sex": r[1], "count": r[2]} for r in rows]


@router.get("/country-dist")
def country_distribution(
    quarter: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_sync_db),
):
    """Return top reporter countries by count."""
    query = """
        SELECT reporter_country, COUNT(*) as count
        FROM demographics
        WHERE is_superseded = FALSE
        AND reporter_country IS NOT NULL AND reporter_country != ''
    """
    
    q_filter, params = build_quarter_filter(quarter)
    query += " " + q_filter + " GROUP BY reporter_country ORDER BY count DESC LIMIT :limit"
    params["limit"] = limit

    result = db.execute(text(query), params)
    rows = result.fetchall()
    return [{"country": r[0], "count": r[1]} for r in rows]


@router.get("/summary")
def demographics_summary(
    quarter: Optional[str] = Query(None),
    db: Session = Depends(get_sync_db),
):
    """Return aggregate demographic statistics."""
    base_where = "WHERE is_superseded = FALSE"
    
    q_filter, params = build_quarter_filter(quarter)
    base_where += " " + q_filter

    r = db.execute(text(f"SELECT COUNT(*) FROM demographics {base_where}"), params)
    total = r.scalar()

    r = db.execute(text(f"""
        SELECT age_group, COUNT(*) as count
        FROM demographics {base_where} AND age_group IS NOT NULL
        GROUP BY age_group ORDER BY count DESC
    """), params)
    age_groups = {row[0]: row[1] for row in r.fetchall()}

    r = db.execute(text(f"""
        SELECT sex, COUNT(*) as count
        FROM demographics {base_where} AND sex IS NOT NULL
        GROUP BY sex
    """), params)
    sex_dist = {row[0]: row[1] for row in r.fetchall()}

    r = db.execute(text(f"""
        SELECT AVG(age_years), MIN(age_years), MAX(age_years), COUNT(age_years)
        FROM demographics {base_where} AND age_years IS NOT NULL
    """), params)
    age_stats = r.fetchone()

    r = db.execute(text(
        "SELECT DISTINCT source_quarter FROM demographics "
        "WHERE is_superseded = FALSE ORDER BY source_quarter"
    ))
    quarters = [row[0] for row in r.fetchall()]

    return {
        "total_patients": total,
        "age_group_distribution": age_groups,
        "sex_distribution": sex_dist,
        "age_stats": {
            "mean": round(float(age_stats[0]), 2) if age_stats[0] else None,
            "min": round(float(age_stats[1]), 2) if age_stats[1] else None,
            "max": round(float(age_stats[2]), 2) if age_stats[2] else None,
            "age_known_count": int(age_stats[3]) if age_stats[3] else 0,
        },
        "quarters_available": quarters,
        "active_quarter": quarter or "ALL",
    }
