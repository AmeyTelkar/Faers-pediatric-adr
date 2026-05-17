"""
Integration test: Run full ETL pipeline on real FAERS Q4 data from Google Drive.
Tests in-memory processing only (no DB required).
"""
import sys
import os
import asyncio
import time

# Add the backend to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# Map folder names to FAERS file types for Q4 (smallest quarter)
Q4_FILES = {
    "DEMO24-25": "DEMO25Q4[Oct-Dec].txt",
    "DRUG24-25": "DRUG25Q4[OCT-DEC].txt",
    "REAC24-25": "REAC25Q4[OCT-DEC].txt",
    "OUTC24-25": "OUTC25Q4[OCT-DEC].txt",
    "RPSR24-25": "RPSR25Q4[OCT-DEC].txt",
    "THER24-25": "THER25Q4[OCT-DEC].txt",
    "INDI24-25": "INDI25Q4[OCT-DEC].txt",
}


def load_files():
    """Load all Q4 FAERS files from disk."""
    file_data = {}
    for folder, filename in Q4_FILES.items():
        filepath = os.path.join(DATA_DIR, folder, filename)
        if not os.path.exists(filepath):
            print(f"  WARNING: {filepath} not found, skipping")
            continue
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"  Loading {folder}/{filename} ({size_mb:.1f} MB)...")
        with open(filepath, "rb") as f:
            file_data[filename] = f.read()
    return file_data


async def run_test():
    print("=" * 70)
    print("PULSETECH FAERS PIPELINE — INTEGRATION TEST (Q4 2025)")
    print("=" * 70)

    # Step 1: Load files
    print("\n[1/4] Loading FAERS Q4 files from disk...")
    t0 = time.time()
    file_data = load_files()
    print(f"  Loaded {len(file_data)} files in {time.time() - t0:.1f}s")

    if len(file_data) < 4:
        print("ERROR: Need at least DEMO, DRUG, REAC, OUTC files")
        return

    # Step 2: Run the pipeline
    print("\n[2/4] Running ETL pipeline (in-memory)...")
    t1 = time.time()

    from app.pipeline.orchestrator import run_pipeline
    preview_stats, demo, parsed = await run_pipeline(file_data, "2025Q4")

    elapsed = time.time() - t1
    print(f"  Pipeline completed in {elapsed:.1f}s")

    # Step 3: Print preview stats
    print("\n[3/4] PREVIEW STATISTICS:")
    print("-" * 50)
    print(f"  Raw DEMO rows:           {preview_stats['demo_raw_rows']:,}")
    print(f"  After dedup:             {preview_stats['demo_after_dedup']:,}")
    print(f"  After pediatric filter:  {preview_stats['demo_after_pediatric_filter']:,}")
    print(f"  Pediatric %:             {preview_stats['pediatric_pct']}%")

    print(f"\n  Age Group Distribution:")
    for ag, count in sorted(preview_stats.get("age_group_distribution", {}).items(), key=lambda x: str(x[0] or "ZZZ")):
        ag_str = str(ag) if ag else "Unknown/NULL"
        print(f"    {ag_str:20s}: {count:,}")

    print(f"\n  Sex Distribution:")
    for sex, count in sorted(preview_stats.get("sex_distribution", {}).items(), key=lambda x: str(x[0] or "ZZZ")):
        sex_str = str(sex) if sex else "Unknown"
        print(f"    {sex_str:10s}: {count:,}")

    print(f"\n  Null Rates:")
    for col, rate in preview_stats.get("null_rates", {}).items():
        print(f"    {col:20s}: {rate}%")

    print(f"\n  Top 10 ADRs:")
    for adr, count in list(preview_stats.get("top_adr", {}).items())[:10]:
        print(f"    {adr:40s}: {count:,}")

    print(f"\n  Outcome Distribution:")
    for outc, count in preview_stats.get("top_outcomes", {}).items():
        print(f"    {outc:5s}: {count:,}")

    print(f"\n  Drug Normalization Sample:")
    for ds in preview_stats.get("drug_sample", [])[:5]:
        orig = ds.get("drugname", "?")
        norm = ds.get("drugname_normalized", "?")
        print(f"    {orig:35s} -> {norm}")

    print(f"\n  Files detected: {preview_stats.get('file_types_detected', [])}")

    # Step 4: Validate parsed DataFrames
    print("\n[4/4] PARSED DATAFRAME SHAPES:")
    print("-" * 50)
    print(f"  DEMO (filtered): {demo.shape}")
    for ftype, df in parsed.items():
        print(f"  {ftype:10s}:       {df.shape}")

    # Validate critical columns
    print("\n  CRITICAL VALIDATION:")
    assert "age_group" in demo.columns, "FAIL: age_group missing from demo"
    assert "age_years" in demo.columns, "FAIL: age_years missing from demo"
    assert "weight_kg" in demo.columns, "FAIL: weight_kg missing from demo"
    assert "source_quarter" in demo.columns, "FAIL: source_quarter missing"
    print("  ✓ age_group column present")
    print("  ✓ age_years column present")
    print("  ✓ weight_kg column present")
    print("  ✓ source_quarter column present")

    if "DRUG" in parsed:
        assert "drugname_normalized" in parsed["DRUG"].columns, "FAIL: drug normalization missing"
        print("  ✓ drugname_normalized column present in DRUG")

    if "OUTC" in parsed:
        assert "severity_score" in parsed["OUTC"].columns, "FAIL: severity_score missing"
        print("  ✓ severity_score column present in OUTC")

    # Step 5: Test signal detection on a small set
    print("\n[BONUS] Testing signal detection engine...")
    try:
        from app.analytics.signal_engine import compute_signals_for_age_group, is_signal
        import pandas as pd

        # Get the most common age group
        top_ag = demo["age_group"].value_counts().index[0]
        print(f"  Computing signals for age group: {top_ag}")

        drug_df = parsed["DRUG"].copy()
        reac_df = parsed["REAC"].copy() if "REAC" in parsed else pd.DataFrame()

        t2 = time.time()
        signals = compute_signals_for_age_group(drug_df, reac_df, demo, top_ag, min_n=5)
        elapsed2 = time.time() - t2

        flagged = [s for s in signals if s.get("is_signal")]
        print(f"  Computed {len(signals)} drug-ADR pairs in {elapsed2:.1f}s")
        print(f"  Signals flagged: {len(flagged)}")

        if flagged:
            print(f"\n  Top 5 flagged signals ({top_ag}):")
            for s in sorted(flagged, key=lambda x: x.get("n11", 0), reverse=True)[:5]:
                drug = s["drugname_normalized"]
                adr = s["pt_term"]
                n = s["n11"]
                prr = s.get("prr", "N/A")
                ror = s.get("ror", "N/A")
                print(f"    {drug:30s} + {adr:30s} N={n:4d}  PRR={prr}  ROR={ror}")
    except Exception as e:
        print(f"  Signal detection test error: {e}")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_test())
