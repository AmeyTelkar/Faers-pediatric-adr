"""
Reactions Router — SOC heatmap, top PT terms, drug-ADR pairs.
Uses SYNC database session for fast JOIN queries.
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_sync_db
from app.routers.utils import build_quarter_filter

router = APIRouter()

import json
import os
import time

# Create a local cache directory for reactions
REACTIONS_CACHE_DIR = "reaction_cache_data"
if not os.path.exists(REACTIONS_CACHE_DIR):
    os.makedirs(REACTIONS_CACHE_DIR)

def get_disk_cache(key: str):
    filepath = os.path.join(REACTIONS_CACHE_DIR, f"{key}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def set_disk_cache(key: str, data):
    filepath = os.path.join(REACTIONS_CACHE_DIR, f"{key}.json")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception:
        pass
@router.get("/top-pt")
def top_pt_terms(
    age_group: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_sync_db),
):
    """Top preferred terms (ADRs) by report count."""
    cache_key = f"top_pt_{age_group}_{quarter}_{limit}"
    cached = get_disk_cache(cache_key)
    if cached is not None:
        return cached

    query = """
        SELECT r.pt_term, COUNT(*) as count
        FROM reactions r
        JOIN demographics d ON r.primaryid = d.primaryid
        WHERE r.pt_term IS NOT NULL
        AND r.is_superseded = FALSE AND d.is_superseded = FALSE
    """
    params = {}
    if age_group:
        query += " AND d.age_group = :age_group"
        params["age_group"] = age_group
        
    q_filter, q_params = build_quarter_filter(quarter, "r.")
    if q_filter:
        query += " " + q_filter
        params.update(q_params)

    query += " GROUP BY r.pt_term ORDER BY count DESC LIMIT :limit"
    params["limit"] = limit

    result = db.execute(text(query), params)
    rows = result.fetchall()
    
    out = [{"pt_term": r[0], "count": r[1]} for r in rows]
    set_disk_cache(cache_key, out)
    return out


@router.get("/soc-heatmap")
def soc_heatmap(
    quarter: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_sync_db),
):
    """ADR counts by age_group x pt_term for heatmap visualization."""
    cache_key = f"soc_heatmap_{quarter}_{limit}"
    cached = get_disk_cache(cache_key)
    if cached is not None:
        return cached

    top_query = """
        SELECT r.pt_term, COUNT(*) as cnt
        FROM reactions r
        JOIN demographics d ON r.primaryid = d.primaryid
        WHERE r.pt_term IS NOT NULL AND d.age_group IS NOT NULL
        AND r.is_superseded = FALSE AND d.is_superseded = FALSE
    """
    params = {}
    
    q_filter, q_params = build_quarter_filter(quarter, "r.")
    if q_filter:
        top_query += " " + q_filter
        params.update(q_params)

    top_query += " GROUP BY r.pt_term ORDER BY cnt DESC LIMIT :limit"
    params["limit"] = limit

    result = db.execute(text(top_query), params)
    top_adrs = [r[0] for r in result.fetchall()]

    if not top_adrs:
        return []

    placeholders = ", ".join([f":adr_{i}" for i in range(len(top_adrs))])
    heatmap_query = f"""
        SELECT d.age_group, r.pt_term, COUNT(*) as count
        FROM reactions r
        JOIN demographics d ON r.primaryid = d.primaryid
        WHERE r.pt_term IN ({placeholders})
        AND d.age_group IS NOT NULL
        AND r.is_superseded = FALSE AND d.is_superseded = FALSE
    """
    adr_params = {f"adr_{i}": adr for i, adr in enumerate(top_adrs)}
    adr_params.update(params)
    if "limit" in adr_params:
        del adr_params["limit"]

    if q_filter:
        heatmap_query += " " + q_filter
        adr_params.update(q_params)
    heatmap_query += " GROUP BY d.age_group, r.pt_term ORDER BY d.age_group, count DESC"

    result = db.execute(text(heatmap_query), adr_params)
    rows = result.fetchall()
    
    out = [{"age_group": r[0], "pt_term": r[1], "count": r[2]} for r in rows]
    set_disk_cache(cache_key, out)
    return out


@router.get("/drug-adr-pairs")
def drug_adr_pairs(
    age_group: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    min_count: int = Query(3, ge=1),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_sync_db),
):
    """Top drug-ADR co-occurrence pairs (Primary Suspect only)."""
    cache_key = f"drug_adr_pairs_{age_group}_{quarter}_{min_count}_{limit}"
    cached = get_disk_cache(cache_key)
    if cached is not None:
        return cached

    query = """
        SELECT dr.drugname_normalized, r.pt_term, d.age_group, COUNT(*) as count
        FROM drugs dr
        JOIN reactions r ON dr.primaryid = r.primaryid
        JOIN demographics d ON dr.primaryid = d.primaryid
        WHERE dr.role_cod = 'PS'
        AND dr.drugname_normalized IS NOT NULL
        AND r.pt_term IS NOT NULL
        AND d.age_group IS NOT NULL
        AND dr.is_superseded = FALSE AND r.is_superseded = FALSE AND d.is_superseded = FALSE
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
        GROUP BY dr.drugname_normalized, r.pt_term, d.age_group
        HAVING COUNT(*) >= :min_count
        ORDER BY count DESC
        LIMIT :limit
    """
    params["min_count"] = min_count
    params["limit"] = limit

    result = db.execute(text(query), params)
    rows = result.fetchall()
    
    out = [
        {"drug": r[0], "adr": r[1], "age_group": r[2], "count": r[3]}
        for r in rows
    ]
    set_disk_cache(cache_key, out)
    return out
