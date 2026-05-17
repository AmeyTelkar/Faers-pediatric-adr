"""
Signals Router — compute, cache, and serve signal detection results.
Uses SYNC database session for fast JOIN queries.
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_sync_db
from app.routers.utils import build_quarter_filter

router = APIRouter()


@router.get("/compute")
def compute_signals(
    age_group: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    min_n: int = Query(3, ge=1),
    drug: Optional[str] = Query(None),
    adr: Optional[str] = Query(None),
    signal_only: bool = Query(False),
    limit: int = Query(100, le=5000),
    db: Session = Depends(get_sync_db),
):
    """Return signal_cache rows. If cache is empty, trigger recompute."""
    qf = quarter if quarter and quarter != "ALL" else "ALL"

    count_result = db.execute(text(
        "SELECT COUNT(*) FROM signal_cache WHERE quarter_filter = :qf"
    ), {"qf": qf})
    cache_count = count_result.scalar()

    if cache_count == 0:
        _recompute_signals(db, min_n, quarter_filter=qf)

    query = "SELECT * FROM signal_cache WHERE n11 >= :min_n AND quarter_filter = :qf"
    params = {"min_n": min_n, "qf": qf}

    if age_group:
        # Support comma-separated age groups using IN clause
        ag_list = [ag.strip() for ag in age_group.split(',')]
        placeholders = ", ".join([f":ag_{i}" for i in range(len(ag_list))])
        query += f" AND age_group IN ({placeholders})"
        for i, ag in enumerate(ag_list):
            params[f"ag_{i}"] = ag
    if drug:
        query += " AND drugname_normalized ILIKE :drug"
        params["drug"] = f"%{drug}%"
    if adr:
        query += " AND pt_term ILIKE :adr"
        params["adr"] = f"%{adr}%"
    if signal_only:
        query += """ AND (
            (prr >= 2 AND prr_chi2 >= 4) OR
            (ror >= 2 AND ror_ci_lower > 1) OR
            (ic025 > 0) OR
            (eb05 > 2)
        )"""

    query += " ORDER BY n11 DESC LIMIT :limit"
    params["limit"] = limit

    result = db.execute(text(query), params)
    rows = result.fetchall()
    columns = result.keys()

    return [dict(zip(columns, row)) for row in rows]


@router.get("/top-drugs")
def top_drugs(
    age_group: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_sync_db),
):
    """Top suspect drugs by report count for given age group."""
    query = """
        SELECT dr.drugname_normalized, COUNT(DISTINCT dr.primaryid) as report_count
        FROM drugs dr
        JOIN demographics d ON dr.primaryid = d.primaryid
        WHERE dr.role_cod = 'PS'
        AND dr.drugname_normalized IS NOT NULL
        AND dr.is_superseded = FALSE AND d.is_superseded = FALSE
    """
    params = {}
    if age_group:
        query += " AND d.age_group = :age_group"
        params["age_group"] = age_group
        
    q_filter, q_params = build_quarter_filter(quarter, "dr.")
    if q_filter:
        query += " " + q_filter
        params.update(q_params)
    query += " GROUP BY dr.drugname_normalized ORDER BY report_count DESC LIMIT :limit"
    params["limit"] = limit

    result = db.execute(text(query), params)
    rows = result.fetchall()
    return [{"drug": r[0], "report_count": r[1]} for r in rows]


@router.post("/recompute")
def recompute_signals(
    quarter: Optional[str] = Query("ALL"),
    min_n: int = Query(3, ge=1),
    db: Session = Depends(get_sync_db),
):
    """Force-rebuild signal_cache."""
    qf = quarter if quarter and quarter != "ALL" else "ALL"
    count = _recompute_signals(db, min_n, quarter_filter=qf)
    return {"status": "completed", "signals_computed": count, "quarter_filter": qf}


def _recompute_signals(db: Session, min_n: int = 3, quarter_filter: str = "ALL") -> int:
    """Internal function to recompute all signals and populate cache."""
    import pandas as pd
    from app.analytics.signal_engine import compute_signals_for_age_group

    # Build quarter SQL filter using utility
    q_filter, q_params = build_quarter_filter(quarter_filter)
    q_where = "AND is_superseded = FALSE"
    if q_filter:
        q_where += " " + q_filter

    # Load data from DB (active rows only)
    demo_result = db.execute(text(
        f"SELECT primaryid, age_group FROM demographics WHERE age_group IS NOT NULL {q_where}"
    ), q_params)
    demo_df = pd.DataFrame(demo_result.fetchall(), columns=["primaryid", "age_group"])

    drug_result = db.execute(text(
        f"SELECT primaryid, drugname_normalized, role_cod FROM drugs WHERE is_superseded = FALSE {q_filter}"
    ), q_params)
    drug_df = pd.DataFrame(drug_result.fetchall(), columns=["primaryid", "drugname_normalized", "role_cod"])

    reac_result = db.execute(text(
        f"SELECT primaryid, pt_term FROM reactions WHERE is_superseded = FALSE {q_filter}"
    ), q_params)
    reac_df = pd.DataFrame(reac_result.fetchall(), columns=["primaryid", "pt_term"])

    if demo_df.empty or drug_df.empty or reac_df.empty:
        return 0

    q_result = db.execute(text(
        "SELECT DISTINCT source_quarter FROM demographics WHERE is_superseded = FALSE"
    ))
    quarters = [r[0] for r in q_result.fetchall()]

    # Clear existing cache for this quarter_filter
    db.execute(text(
        "DELETE FROM signal_cache WHERE quarter_filter = :qf"
    ), {"qf": quarter_filter})

    # Compute for each age group
    age_groups = demo_df["age_group"].unique().tolist()
    total_signals = 0

    for ag in age_groups:
        print(f"  [SIGNAL] Computing signals for {ag} (filter={quarter_filter})...")
        signals = compute_signals_for_age_group(drug_df, reac_df, demo_df, ag, min_n)

        for s in signals:
            db.execute(text("""
                INSERT INTO signal_cache (
                    drugname_normalized, pt_term, age_group,
                    n11, n1x, nx1, nxx,
                    prr, prr_ci_lower, prr_chi2,
                    ror, ror_ci_lower, ror_ci_upper,
                    ic, ic025, ebgm, eb05,
                    source_quarters, quarter_filter
                ) VALUES (
                    :drugname_normalized, :pt_term, :age_group,
                    :n11, :n1x, :nx1, :nxx,
                    :prr, :prr_ci_lower, :prr_chi2,
                    :ror, :ror_ci_lower, :ror_ci_upper,
                    :ic, :ic025, :ebgm, :eb05,
                    :source_quarters, :quarter_filter
                ) ON CONFLICT (drugname_normalized, pt_term, age_group, quarter_filter)
                DO UPDATE SET
                    n11 = EXCLUDED.n11, n1x = EXCLUDED.n1x,
                    nx1 = EXCLUDED.nx1, nxx = EXCLUDED.nxx,
                    prr = EXCLUDED.prr, prr_ci_lower = EXCLUDED.prr_ci_lower,
                    prr_chi2 = EXCLUDED.prr_chi2,
                    ror = EXCLUDED.ror, ror_ci_lower = EXCLUDED.ror_ci_lower,
                    ror_ci_upper = EXCLUDED.ror_ci_upper,
                    ic = EXCLUDED.ic, ic025 = EXCLUDED.ic025,
                    ebgm = EXCLUDED.ebgm, eb05 = EXCLUDED.eb05,
                    computed_at = NOW()
            """), {
                "drugname_normalized": s["drugname_normalized"],
                "pt_term": s["pt_term"],
                "age_group": s["age_group"],
                "n11": s["n11"], "n1x": s["n1x"],
                "nx1": s["nx1"], "nxx": s["nxx"],
                "prr": s.get("prr"), "prr_ci_lower": s.get("prr_ci_lower"),
                "prr_chi2": s.get("prr_chi2"),
                "ror": s.get("ror"), "ror_ci_lower": s.get("ror_ci_lower"),
                "ror_ci_upper": s.get("ror_ci_upper"),
                "ic": s.get("ic"), "ic025": s.get("ic025"),
                "ebgm": s.get("ebgm"), "eb05": s.get("eb05"),
                "source_quarters": quarters,
                "quarter_filter": quarter_filter,
            })
            total_signals += 1

    db.commit()

    # Update signal_count in loaded_quarters
    try:
        if quarter_filter == "ALL":
            db.execute(text("""
                UPDATE loaded_quarters SET signal_count = :cnt
                WHERE quarter = (SELECT quarter FROM loaded_quarters ORDER BY year DESC, quarter_num DESC LIMIT 1)
            """), {"cnt": total_signals})
        elif quarter_filter.endswith('_ALL'):
            pass  # Do not overwrite quarter-level signal counts with year-level aggregated totals
        else:
            db.execute(text(
                "UPDATE loaded_quarters SET signal_count = :cnt WHERE quarter = :q"
            ), {"cnt": total_signals, "q": quarter_filter})
        db.commit()
    except Exception:
        pass

    print(f"  [SIGNAL] Total: {total_signals} signals computed (filter={quarter_filter})")
    return total_signals
