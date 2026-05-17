"""
Upload Router — file ingestion, task polling, approve/reject.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import uuid
import asyncio
import traceback
from app.pipeline.orchestrator import run_pipeline

router = APIRouter()

# In-memory store for pipeline results awaiting approval
_pipeline_store: dict = {}


async def _run_pipeline_background(task_id: str, file_data: dict, quarter: str, year: int, filenames: list):
    """Run the pipeline in the background so /ingest returns immediately."""
    try:
        preview_stats, demo, parsed = await run_pipeline(file_data, quarter)

        _pipeline_store[task_id] = {
            "status": "ready",
            "preview": preview_stats,
            "demo": demo,
            "parsed": parsed,
            "quarter": quarter,
            "year": year,
            "filenames": filenames,
        }
        print(f"  [UPLOAD] Pipeline {task_id[:8]} completed successfully.")
    except Exception as e:
        print(f"  [UPLOAD] Pipeline {task_id[:8]} FAILED: {e}")
        traceback.print_exc()
        _pipeline_store[task_id] = {
            "status": "failed",
            "error": str(e),
            "filenames": filenames,
        }


@router.post("/ingest")
async def ingest_files(
    files: List[UploadFile] = File(...),
    quarter: str = Form(...),
    year: int = Form(...),
):
    """
    Accepts up to 7 FAERS .txt files.
    Reads file bytes, then kicks off the pipeline as a background task.
    Returns task_id immediately for polling via /task/{task_id}.
    """
    if not 1 <= len(files) <= 7:
        raise HTTPException(400, "Upload between 1 and 7 FAERS files.")

    task_id = str(uuid.uuid4())
    file_data = {}
    filenames = []
    for f in files:
        content = await f.read()
        file_data[f.filename] = content
        filenames.append(f.filename)

    total_mb = sum(len(v) for v in file_data.values()) / (1024 * 1024)
    print(f"  [UPLOAD] Received {len(files)} files ({total_mb:.1f} MB). Task: {task_id[:8]}")

    # Store task as pending
    _pipeline_store[task_id] = {"status": "processing", "filenames": filenames}

    # Fire-and-forget: run pipeline in background so this endpoint returns immediately
    asyncio.create_task(_run_pipeline_background(task_id, file_data, quarter, year, filenames))

    return {"task_id": task_id, "status": "processing"}


@router.get("/task/{task_id}")
async def task_status(task_id: str):
    """Poll ETL task status and preview stats."""
    result = _pipeline_store.get(task_id)
    if not result:
        raise HTTPException(404, f"Task {task_id} not found")

    if result["status"] == "ready":
        return {"status": "ready", "preview": result["preview"]}
    elif result["status"] == "failed":
        return {"status": "failed", "error": result.get("error", "Unknown error")}
    return {"status": result["status"]}


@router.post("/approve/{task_id}")
async def approve_upload(task_id: str):
    """User approves preview -> push to PostgreSQL using fast COPY."""
    import pandas as pd
    import time
    import io as _io
    from sqlalchemy import create_engine, text
    from app.config import settings

    result = _pipeline_store.get(task_id)
    if not result or result["status"] != "ready":
        raise HTTPException(400, "Task not ready for approval")

    session_id = str(uuid.uuid4())
    demo = result["demo"]
    parsed = result["parsed"]
    quarter = result["quarter"]
    year = result["year"]

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2").replace("asyncpg", "psycopg2")
    if "psycopg2" not in sync_url:
        sync_url = settings.DATABASE_URL_SYNC
    engine = create_engine(sync_url)

    try:
        insert_start = time.perf_counter()
        CHUNK = 5000

        # 1. Create upload session FIRST
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO upload_sessions (session_id, quarter, year, files_uploaded, status)
                VALUES (:sid, :q, :y, :files, 'approved')
            """), {
                "sid": session_id,
                "q": quarter,
                "y": year,
                "files": list(parsed.keys()),
            })
        print(f"  [DB] upload_session created: {session_id[:8]}")

        # 1.5. Clean duplicate identical caseversions (same primaryid)
        demo_insert = demo.copy()
        demo_insert["primaryid"] = pd.to_numeric(demo_insert["primaryid"], errors="coerce")
        pids_in_upload = demo_insert["primaryid"].dropna().unique().tolist()
        existing_pids = set()

        if pids_in_upload:
            with engine.connect() as conn:
                chunk_size = 20000
                for i in range(0, len(pids_in_upload), chunk_size):
                    chunk = pids_in_upload[i:i+chunk_size]
                    res = conn.execute(
                        text("SELECT primaryid FROM demographics WHERE primaryid = ANY(:pids)"),
                        {"pids": chunk}
                    ).fetchall()
                    for r in res:
                        existing_pids.add(r[0])
                        
        if existing_pids:
            print(f"  [DB] Dropping {len(existing_pids):,} exact duplicates across tables.")
            demo_insert = demo_insert[~demo_insert["primaryid"].isin(existing_pids)]

        # 2. Insert demographics
        demo_insert["session_id"] = session_id
        demo_insert["caseid"] = pd.to_numeric(demo_insert["caseid"], errors="coerce")
        demo_insert["caseversion"] = pd.to_numeric(demo_insert.get("caseversion", pd.Series()), errors="coerce")
        demo_cols = [
            "primaryid", "caseid", "caseversion", "i_f_code", "event_dt", "fda_dt",
            "rept_cod", "age_raw", "age_cod", "age_years", "age_group",
            "is_age_imputed", "sex", "weight_kg", "occp_cod", "reporter_country",
            "occr_country", "event_dt_partial", "source_quarter", "session_id",
        ]
        for col in demo_cols:
            if col not in demo_insert.columns:
                demo_insert[col] = None
        t0 = time.perf_counter()
        demo_insert[demo_cols].to_sql("demographics", engine, if_exists="append", index=False, chunksize=CHUNK, method="multi")
        print(f"  [DB] demographics: {len(demo_insert):,} rows ({time.perf_counter()-t0:.1f}s)")

        # 3. Insert drugs
        if "DRUG" in parsed:
            drug_df = parsed["DRUG"].copy()
            drug_df["primaryid"] = pd.to_numeric(drug_df["primaryid"], errors="coerce")
            if existing_pids:
                drug_df = drug_df[~drug_df["primaryid"].isin(existing_pids)]
            drug_df["caseid"] = pd.to_numeric(drug_df["caseid"], errors="coerce")
            drug_df["drug_seq"] = pd.to_numeric(drug_df["drug_seq"], errors="coerce")
            if "drugname" in drug_df.columns and "drugname_original" not in drug_df.columns:
                drug_df = drug_df.rename(columns={"drugname": "drugname_original"})
            drug_cols = [
                "primaryid", "caseid", "drug_seq", "role_cod", "drugname_original",
                "drugname_normalized", "rxcui", "route", "dose_amt", "dose_unit",
                "dose_form", "dose_freq", "dechal", "rechal", "source_quarter",
            ]
            for col in drug_cols:
                if col not in drug_df.columns:
                    drug_df[col] = None
            t0 = time.perf_counter()
            drug_df[drug_cols].to_sql("drugs", engine, if_exists="append", index=False, chunksize=CHUNK, method="multi")
            print(f"  [DB] drugs: {len(drug_df):,} rows ({time.perf_counter()-t0:.1f}s)")

        # 4. Insert reactions
        if "REAC" in parsed:
            reac_df = parsed["REAC"].copy()
            reac_df["primaryid"] = pd.to_numeric(reac_df["primaryid"], errors="coerce")
            if existing_pids:
                reac_df = reac_df[~reac_df["primaryid"].isin(existing_pids)]
            reac_df["caseid"] = pd.to_numeric(reac_df["caseid"], errors="coerce")
            if "pt" in reac_df.columns and "pt_term" not in reac_df.columns:
                reac_df = reac_df.rename(columns={"pt": "pt_term"})
            reac_cols = ["primaryid", "caseid", "pt_term", "drug_rec_act", "source_quarter"]
            for col in reac_cols:
                if col not in reac_df.columns:
                    reac_df[col] = None
            t0 = time.perf_counter()
            reac_df[reac_cols].to_sql("reactions", engine, if_exists="append", index=False, chunksize=CHUNK, method="multi")
            print(f"  [DB] reactions: {len(reac_df):,} rows ({time.perf_counter()-t0:.1f}s)")

        # 5. Insert outcomes
        if "OUTC" in parsed:
            outc_df = parsed["OUTC"].copy()
            outc_df["primaryid"] = pd.to_numeric(outc_df["primaryid"], errors="coerce")
            if existing_pids:
                outc_df = outc_df[~outc_df["primaryid"].isin(existing_pids)]
            outc_df["caseid"] = pd.to_numeric(outc_df["caseid"], errors="coerce")
            outc_cols = ["primaryid", "caseid", "outc_cod", "severity_score", "source_quarter"]
            for col in outc_cols:
                if col not in outc_df.columns:
                    outc_df[col] = None
            t0 = time.perf_counter()
            outc_df[outc_cols].to_sql("outcomes", engine, if_exists="append", index=False, chunksize=CHUNK, method="multi")
            print(f"  [DB] outcomes: {len(outc_df):,} rows ({time.perf_counter()-t0:.1f}s)")

        # 6. Insert report sources
        if "RPSR" in parsed:
            rpsr_df = parsed["RPSR"].copy()
            rpsr_df["primaryid"] = pd.to_numeric(rpsr_df["primaryid"], errors="coerce")
            if existing_pids:
                rpsr_df = rpsr_df[~rpsr_df["primaryid"].isin(existing_pids)]
            rpsr_df["caseid"] = pd.to_numeric(rpsr_df["caseid"], errors="coerce")
            rpsr_cols = ["primaryid", "caseid", "rpsr_cod", "source_quarter"]
            for col in rpsr_cols:
                if col not in rpsr_df.columns:
                    rpsr_df[col] = None
            t0 = time.perf_counter()
            rpsr_df[rpsr_cols].to_sql("report_sources", engine, if_exists="append", index=False, chunksize=CHUNK, method="multi")
            print(f"  [DB] report_sources: {len(rpsr_df):,} rows ({time.perf_counter()-t0:.1f}s)")

        # 7. Insert therapy
        if "THER" in parsed:
            from app.pipeline.date_handler import handle_dates
            ther_df = parsed["THER"].copy()
            ther_df["primaryid"] = pd.to_numeric(ther_df["primaryid"], errors="coerce")
            if existing_pids:
                ther_df = ther_df[~ther_df["primaryid"].isin(existing_pids)]
            ther_df["caseid"] = pd.to_numeric(ther_df["caseid"], errors="coerce")
            ther_df["dsg_drug_seq"] = pd.to_numeric(ther_df.get("dsg_drug_seq", pd.Series()), errors="coerce")
            ther_df = handle_dates(ther_df, date_cols=["start_dt", "end_dt"])
            if "dur" in ther_df.columns and "dur_cod" in ther_df.columns:
                dur_map = {"YR": 365.25, "MON": 30.44, "WK": 7, "DAY": 1, "HR": 1/24}
                dur_val = pd.to_numeric(ther_df["dur"], errors="coerce")
                dur_mult = ther_df["dur_cod"].fillna("").str.upper().map(dur_map)
                ther_df["duration_days"] = dur_val * dur_mult
            else:
                ther_df["duration_days"] = None
            ther_cols = [
                "primaryid", "caseid", "dsg_drug_seq", "start_dt", "end_dt",
                "duration_days", "start_dt_partial", "end_dt_partial", "source_quarter",
            ]
            for col in ther_cols:
                if col not in ther_df.columns:
                    ther_df[col] = None
            t0 = time.perf_counter()
            ther_df[ther_cols].to_sql("therapy", engine, if_exists="append", index=False, chunksize=CHUNK, method="multi")
            print(f"  [DB] therapy: {len(ther_df):,} rows ({time.perf_counter()-t0:.1f}s)")

        # 8. Insert indications
        if "INDI" in parsed:
            indi_df = parsed["INDI"].copy()
            indi_df["primaryid"] = pd.to_numeric(indi_df["primaryid"], errors="coerce")
            if existing_pids:
                indi_df = indi_df[~indi_df["primaryid"].isin(existing_pids)]
            indi_df["caseid"] = pd.to_numeric(indi_df["caseid"], errors="coerce")
            if "indi_drug_seq" in indi_df.columns and "drug_seq" not in indi_df.columns:
                indi_df["drug_seq"] = indi_df["indi_drug_seq"]
            indi_df["drug_seq"] = pd.to_numeric(indi_df.get("drug_seq", pd.Series()), errors="coerce")
            indi_cols = ["primaryid", "caseid", "drug_seq", "indi_pt", "source_quarter"]
            for col in indi_cols:
                if col not in indi_df.columns:
                    indi_df[col] = None
            t0 = time.perf_counter()
            indi_df[indi_cols].to_sql("indications", engine, if_exists="append", index=False, chunksize=CHUNK, method="multi")
            print(f"  [DB] indications: {len(indi_df):,} rows ({time.perf_counter()-t0:.1f}s)")

        # ── 9. Cross-quarter deduplication ──────────────────────────────
        from app.pipeline.deduplicator import run_cross_quarter_dedup
        dedup_result = run_cross_quarter_dedup(quarter)

        # ── 10. Register in loaded_quarters ────────────────────────────
        with engine.begin() as conn:
            # Extract quarter number from string like '2025Q2' -> 2
            q_num = int(quarter[-1]) if quarter[-1].isdigit() else 1
            q_labels = {1: 'Jul–Sep', 2: 'Oct–Dec', 3: 'Jan–Mar', 4: 'Apr–Jun'}
            q_label = f"Q{q_num} {year} ({q_labels.get(q_num, '')})"

            conn.execute(text("""
                INSERT INTO loaded_quarters
                (quarter, year, quarter_num, quarter_label,
                 pediatric_rows, drug_rows, reaction_rows,
                 superseded_rows, session_id)
                VALUES (:q, :yr, :qn, :ql, :ped, :drg, :rac, :sup, :sid)
                ON CONFLICT (quarter) DO UPDATE SET
                    pediatric_rows = EXCLUDED.pediatric_rows,
                    drug_rows = EXCLUDED.drug_rows,
                    reaction_rows = EXCLUDED.reaction_rows,
                    superseded_rows = EXCLUDED.superseded_rows,
                    loaded_at = NOW()
            """), {
                "q": quarter, "yr": year, "qn": q_num, "ql": q_label,
                "ped": len(demo_insert),
                "drg": len(parsed.get("DRUG", [])),
                "rac": len(parsed.get("REAC", [])),
                "sup": dedup_result.get("superseded", 0),
                "sid": session_id,
            })

        # Cleanup
        del _pipeline_store[task_id]
        from app.core.cache import invalidate_all_report_cache
        invalidate_all_report_cache()
        total_insert = time.perf_counter() - insert_start
        print(f"  [DB] ALL TABLES COMMITTED in {total_insert:.1f}s")

        return {
            "status": "committed",
            "session_id": session_id,
            "quarter": quarter,
            "insert_time_seconds": round(total_insert, 1),
            "cross_quarter_dedup": dedup_result,
        }

    except Exception as e:
        raise HTTPException(500, f"DB commit failed: {str(e)}")
    finally:
        engine.dispose()


@router.post("/reject/{task_id}")
async def reject_upload(task_id: str):
    """User rejects preview → discard pipeline result."""
    if task_id in _pipeline_store:
        del _pipeline_store[task_id]
    return {"status": "discarded"}


@router.get("/sessions")
async def list_sessions():
    """List all upload sessions from database."""
    from sqlalchemy import create_engine, text
    from app.config import settings

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    if "psycopg2" not in sync_url:
        sync_url = settings.DATABASE_URL_SYNC
    engine = create_engine(sync_url)

    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT session_id, quarter, year, files_uploaded, status, created_at "
                "FROM upload_sessions ORDER BY created_at DESC"
            ))
            sessions = []
            for row in result:
                sessions.append({
                    "session_id": str(row[0]),
                    "quarter": row[1],
                    "year": row[2],
                    "files_uploaded": row[3],
                    "status": row[4],
                    "created_at": str(row[5]) if row[5] else None,
                })
            return sessions
    finally:
        engine.dispose()
