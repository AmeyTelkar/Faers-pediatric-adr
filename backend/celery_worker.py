"""
Celery Worker — wraps pipeline orchestrator as async Celery tasks.
"""
import asyncio
import uuid
import pickle
from celery import Celery
from app.config import settings

app = Celery("faers_worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

app.conf.update(
    task_serializer="pickle",
    result_serializer="pickle",
    accept_content=["pickle", "json"],
    result_expires=3600,  # 1 hour
    task_track_started=True,
)

# Store pipeline results in memory (for preview before approval)
pipeline_results = {}


@app.task(bind=True, name="run_pipeline_task")
def run_pipeline_task(self, file_data: dict, quarter: str, year: int):
    """
    Run the full ETL pipeline as a Celery task.
    Stores results in pipeline_results dict for later approval.
    """
    from app.pipeline.orchestrator import run_pipeline

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        preview_stats, demo, parsed = loop.run_until_complete(
            run_pipeline(file_data, quarter)
        )
        # Store DataFrames for later DB commit
        pipeline_results[self.request.id] = {
            "demo": demo,
            "parsed": parsed,
            "quarter": quarter,
            "year": year,
        }
        return preview_stats
    finally:
        loop.close()


@app.task(bind=True, name="commit_to_db_task")
def commit_to_db_task(self, pipeline_task_id: str, session_id: str):
    """
    Commit approved pipeline results to PostgreSQL.
    """
    import pandas as pd
    from sqlalchemy import create_engine
    from app.config import settings

    result_data = pipeline_results.get(pipeline_task_id)
    if not result_data:
        raise ValueError(f"No pipeline results found for task {pipeline_task_id}")

    demo = result_data["demo"]
    parsed = result_data["parsed"]
    quarter = result_data["quarter"]
    year = result_data["year"]

    # Use sync engine for bulk insert
    sync_url = settings.DATABASE_URL_SYNC
    engine = create_engine(sync_url)

    try:
        # 1. Create upload session
        session_df = pd.DataFrame([{
            "session_id": session_id,
            "quarter": quarter,
            "year": year,
            "files_uploaded": list(parsed.keys()),
            "status": "approved",
        }])
        session_df.to_sql("upload_sessions", engine, if_exists="append", index=False)

        # 2. Insert demographics
        demo_cols = [
            "primaryid", "caseid", "caseversion", "i_f_code", "event_dt", "fda_dt",
            "rept_cod", "age_raw", "age_cod", "age_years", "age_group",
            "is_age_imputed", "sex", "weight_kg", "occp_cod", "reporter_country",
            "occr_country", "event_dt_partial", "source_quarter",
        ]
        demo_insert = demo.copy()
        demo_insert["session_id"] = session_id

        # Ensure columns exist
        for col in demo_cols:
            if col not in demo_insert.columns:
                demo_insert[col] = None

        demo_insert["primaryid"] = pd.to_numeric(demo_insert["primaryid"], errors="coerce")
        demo_insert["caseid"] = pd.to_numeric(demo_insert["caseid"], errors="coerce")
        demo_insert["caseversion"] = pd.to_numeric(demo_insert["caseversion"], errors="coerce")

        demo_insert[demo_cols + ["session_id"]].to_sql(
            "demographics", engine, if_exists="append", index=False
        )

        # 3. Insert drugs
        if "DRUG" in parsed:
            drug_df = parsed["DRUG"].copy()
            drug_df["primaryid"] = pd.to_numeric(drug_df["primaryid"], errors="coerce")
            drug_df["caseid"] = pd.to_numeric(drug_df["caseid"], errors="coerce")
            drug_df["drug_seq"] = pd.to_numeric(drug_df["drug_seq"], errors="coerce")
            drug_df = drug_df.rename(columns={"drugname": "drugname_original"})

            drug_cols = [
                "primaryid", "caseid", "drug_seq", "role_cod", "drugname_original",
                "drugname_normalized", "rxcui", "route", "dose_amt", "dose_unit",
                "dose_form", "dose_freq", "dechal", "rechal", "source_quarter",
            ]
            for col in drug_cols:
                if col not in drug_df.columns:
                    drug_df[col] = None

            drug_df[drug_cols].to_sql("drugs", engine, if_exists="append", index=False)

        # 4. Insert reactions
        if "REAC" in parsed:
            reac_df = parsed["REAC"].copy()
            reac_df["primaryid"] = pd.to_numeric(reac_df["primaryid"], errors="coerce")
            reac_df["caseid"] = pd.to_numeric(reac_df["caseid"], errors="coerce")
            reac_df = reac_df.rename(columns={"pt": "pt_term"})

            reac_cols = ["primaryid", "caseid", "pt_term", "drug_rec_act", "source_quarter"]
            for col in reac_cols:
                if col not in reac_df.columns:
                    reac_df[col] = None

            reac_df[reac_cols].to_sql("reactions", engine, if_exists="append", index=False)

        # 5. Insert outcomes
        if "OUTC" in parsed:
            outc_df = parsed["OUTC"].copy()
            outc_df["primaryid"] = pd.to_numeric(outc_df["primaryid"], errors="coerce")
            outc_df["caseid"] = pd.to_numeric(outc_df["caseid"], errors="coerce")

            outc_cols = ["primaryid", "caseid", "outc_cod", "severity_score", "source_quarter"]
            for col in outc_cols:
                if col not in outc_df.columns:
                    outc_df[col] = None

            outc_df[outc_cols].to_sql("outcomes", engine, if_exists="append", index=False)

        # 6. Insert report sources
        if "RPSR" in parsed:
            rpsr_df = parsed["RPSR"].copy()
            rpsr_df["primaryid"] = pd.to_numeric(rpsr_df["primaryid"], errors="coerce")
            rpsr_df["caseid"] = pd.to_numeric(rpsr_df["caseid"], errors="coerce")

            rpsr_cols = ["primaryid", "caseid", "rpsr_cod", "source_quarter"]
            for col in rpsr_cols:
                if col not in rpsr_df.columns:
                    rpsr_df[col] = None

            rpsr_df[rpsr_cols].to_sql("report_sources", engine, if_exists="append", index=False)

        # 7. Insert therapy
        if "THER" in parsed:
            from app.pipeline.date_handler import handle_dates
            ther_df = parsed["THER"].copy()
            ther_df["primaryid"] = pd.to_numeric(ther_df["primaryid"], errors="coerce")
            ther_df["caseid"] = pd.to_numeric(ther_df["caseid"], errors="coerce")
            ther_df["dsg_drug_seq"] = pd.to_numeric(ther_df["dsg_drug_seq"], errors="coerce")
            ther_df = handle_dates(ther_df, date_cols=["start_dt", "end_dt"])

            # Calculate duration in days
            ther_df["duration_days"] = None
            if "dur" in ther_df.columns and "dur_cod" in ther_df.columns:
                dur_map = {"YR": 365.25, "MON": 30.44, "WK": 7, "DAY": 1, "HR": 1/24}
                dur_val = pd.to_numeric(ther_df["dur"], errors="coerce")
                dur_mult = ther_df["dur_cod"].fillna("").str.upper().map(dur_map)
                ther_df["duration_days"] = dur_val * dur_mult

            ther_cols = [
                "primaryid", "caseid", "dsg_drug_seq", "start_dt", "end_dt",
                "duration_days", "start_dt_partial", "end_dt_partial", "source_quarter",
            ]
            for col in ther_cols:
                if col not in ther_df.columns:
                    ther_df[col] = None

            ther_df[ther_cols].to_sql("therapy", engine, if_exists="append", index=False)

        # 8. Insert indications
        if "INDI" in parsed:
            indi_df = parsed["INDI"].copy()
            indi_df["primaryid"] = pd.to_numeric(indi_df["primaryid"], errors="coerce")
            indi_df["caseid"] = pd.to_numeric(indi_df["caseid"], errors="coerce")
            indi_df["drug_seq"] = pd.to_numeric(indi_df.get("drug_seq", indi_df.get("indi_drug_seq")), errors="coerce")

            indi_cols = ["primaryid", "caseid", "drug_seq", "indi_pt", "source_quarter"]
            for col in indi_cols:
                if col not in indi_df.columns:
                    indi_df[col] = None

            indi_df[indi_cols].to_sql("indications", engine, if_exists="append", index=False)

        # Cleanup pipeline results from memory
        del pipeline_results[pipeline_task_id]

        return {"status": "committed", "session_id": session_id, "quarter": quarter}

    except Exception as e:
        raise RuntimeError(f"DB commit failed: {str(e)}")
    finally:
        engine.dispose()
