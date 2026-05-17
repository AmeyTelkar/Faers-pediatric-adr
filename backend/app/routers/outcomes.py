"""
Outcomes Router — severity trends, outcomes by drug.
Uses SYNC database session for fast JOIN queries.
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_sync_db
from app.routers.utils import build_quarter_filter

router = APIRouter()


@router.get("/severity-trend")
def severity_trend(
    age_group: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    db: Session = Depends(get_sync_db),
):
    """Outcome severity distribution by quarter."""
    query = """
        SELECT o.source_quarter, o.outc_cod, o.severity_score, COUNT(*) as count
        FROM outcomes o
        JOIN demographics d ON o.primaryid = d.primaryid
        WHERE o.is_superseded = FALSE AND d.is_superseded = FALSE
    """
    params = {}
    if age_group:
        query += " AND d.age_group = :age_group"
        params["age_group"] = age_group
        
    q_filter, q_params = build_quarter_filter(quarter, "o.")
    if q_filter:
        query += " " + q_filter
        params.update(q_params)

    query += " GROUP BY o.source_quarter, o.outc_cod, o.severity_score ORDER BY o.source_quarter, o.severity_score DESC"

    result = db.execute(text(query), params)
    rows = result.fetchall()
    return [
        {"quarter": r[0], "outc_cod": r[1], "severity_score": r[2], "count": r[3]}
        for r in rows
    ]


@router.get("/by-drug")
def outcomes_by_drug(
    age_group: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_sync_db),
):
    """Max severity outcome per drug (Primary Suspect only)."""
    query = """
        SELECT
            dr.drugname_normalized,
            MAX(o.severity_score) as max_severity,
            COUNT(DISTINCT o.primaryid) as report_count,
            ARRAY_AGG(DISTINCT o.outc_cod) as outcome_codes
        FROM drugs dr
        JOIN outcomes o ON dr.primaryid = o.primaryid
        JOIN demographics d ON dr.primaryid = d.primaryid
        WHERE dr.role_cod = 'PS'
        AND dr.drugname_normalized IS NOT NULL
        AND dr.is_superseded = FALSE AND o.is_superseded = FALSE AND d.is_superseded = FALSE
    """
    params = {}
    if age_group:
        query += " AND d.age_group = :age_group"
        params["age_group"] = age_group
        
    q_filter, q_params = build_quarter_filter(quarter, "dr.")
    if q_filter:
        query += " " + q_filter
        params.update(q_params)

    query += """
        GROUP BY dr.drugname_normalized
        ORDER BY max_severity DESC, report_count DESC
        LIMIT :limit
    """
    params["limit"] = limit

    result = db.execute(text(query), params)
    rows = result.fetchall()
    return [
        {"drug": r[0], "max_severity": r[1], "report_count": r[2], "outcome_codes": r[3]}
        for r in rows
    ]


@router.get("/distribution")
def outcome_distribution(
    age_group: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    db: Session = Depends(get_sync_db),
):
    """Overall outcome code distribution."""
    query = """
        SELECT o.outc_cod, o.severity_score, COUNT(*) as count
        FROM outcomes o
        JOIN demographics d ON o.primaryid = d.primaryid
        WHERE o.is_superseded = FALSE AND d.is_superseded = FALSE
    """
    params = {}
    
    if age_group:
        query += " AND d.age_group = :age_group"
        params["age_group"] = age_group
        
    q_filter, q_params = build_quarter_filter(quarter, "o.")
    if q_filter:
        query += " " + q_filter
        params.update(q_params)

    query += " GROUP BY o.outc_cod, o.severity_score ORDER BY o.severity_score DESC"

    result = db.execute(text(query), params)
    rows = result.fetchall()

    labels = {
        "DE": "Death", "LT": "Life-Threatening", "HO": "Hospitalization",
        "DS": "Disability", "CA": "Congenital Anomaly",
        "RI": "Required Intervention", "OT": "Other Serious",
    }

    return [
        {"outc_cod": r[0], "label": labels.get(r[0], r[0]), "severity_score": r[1], "count": r[2]}
        for r in rows
    ]
