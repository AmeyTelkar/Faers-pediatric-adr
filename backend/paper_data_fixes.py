"""
P0 Fix: Generate updated Table 2 data + GNN-vs-Classical Concordance Ablation
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.database import get_sync_db
from sqlalchemy import text

db = next(get_sync_db())

print("=" * 70)
print("  PART 1: UPDATED TABLE 2 - Loaded Quarters (Live System Statistics)")
print("=" * 70)

result = db.execute(text("""
    SELECT quarter, pediatric_rows, drug_rows, reaction_rows, 
           signal_count, gnn_trained, superseded_rows
    FROM loaded_quarters
    ORDER BY quarter
"""))

rows = result.fetchall()
total_pts = 0
total_drugs = 0
total_reac = 0
total_sigs = 0
total_dedup = 0

print(f"\n  {'Quarter':<10} {'Patients':>10} {'Drugs':>10} {'Reactions':>10} {'Signals':>10} {'Dedup':>8} {'GNN':>10}")
print(f"  {'-'*68}")
for row in rows:
    q, pts, drugs, reacs, sigs, gnn, dedup = row
    total_pts += (pts or 0)
    total_drugs += (drugs or 0)
    total_reac += (reacs or 0)
    total_sigs += (sigs or 0)
    total_dedup += (dedup or 0)
    gnn_str = "TRAINED" if gnn else "Pending"
    print(f"  {q:<10} {pts or 0:>10,} {drugs or 0:>10,} {reacs or 0:>10,} {sigs or 0:>10,} {dedup or 0:>8,} {gnn_str:>10}")

print(f"  {'-'*68}")
print(f"  {'TOTAL':<10} {total_pts:>10,} {total_drugs:>10,} {total_reac:>10,} {total_sigs:>10,} {total_dedup:>8,}")

active = db.execute(text("SELECT COUNT(*) FROM demographics WHERE is_superseded = FALSE")).scalar()
print(f"\n  Active pediatric patients (non-superseded): {active:,}")
print(f"  Total records (including superseded): {active + total_dedup:,}")

print(f"\n\n{'=' * 70}")
print("  PART 2: SIGNAL DETECTION STATISTICS")
print("=" * 70)

total_sc = db.execute(text("SELECT COUNT(*) FROM signal_cache")).scalar()
print(f"\n  Total signal_cache entries (all drug-ADR-age triples): {total_sc:,}")

for method, condition in [
    ("PRR >= 2 + chi2 >= 4", "prr >= 2 AND prr_chi2 >= 4"),
    ("ROR >= 2 + CI_lower > 1", "ror >= 2 AND ror_ci_lower > 1"),
    ("IC025 > 0", "ic025 > 0"),
    ("EB05 > 2 (EBGM)", "eb05 > 2"),
]:
    count = db.execute(text(f"""
        SELECT COUNT(DISTINCT (drugname_normalized, pt_term, age_group)) 
        FROM signal_cache WHERE {condition}
    """)).scalar()
    print(f"    {method}: {count:,} unique signals")

any_method = db.execute(text("""
    SELECT COUNT(DISTINCT (drugname_normalized, pt_term, age_group))
    FROM signal_cache
    WHERE (prr >= 2 AND prr_chi2 >= 4)
       OR (ror >= 2 AND ror_ci_lower > 1)
       OR (ic025 > 0)
       OR (eb05 > 2)
""")).scalar()
print(f"\n  Total unique signals (flagged by ANY method): {any_method:,}")

for n_methods in [2, 3, 4]:
    count = db.execute(text(f"""
        SELECT COUNT(DISTINCT (drugname_normalized, pt_term, age_group))
        FROM signal_cache
        WHERE (CASE WHEN prr >= 2 AND prr_chi2 >= 4 THEN 1 ELSE 0 END
             + CASE WHEN ror >= 2 AND ror_ci_lower > 1 THEN 1 ELSE 0 END
             + CASE WHEN ic025 > 0 THEN 1 ELSE 0 END
             + CASE WHEN eb05 > 2 THEN 1 ELSE 0 END) >= {n_methods}
    """)).scalar()
    print(f"  Confirmed by >= {n_methods} methods: {count:,}")

print(f"\n  Signals by age group:")
age_sigs = db.execute(text("""
    SELECT age_group, COUNT(DISTINCT (drugname_normalized, pt_term)) as sig_count
    FROM signal_cache 
    WHERE (prr >= 2 AND prr_chi2 >= 4) OR (ror >= 2 AND ror_ci_lower > 1) OR (ic025 > 0) OR (eb05 > 2)
    GROUP BY age_group ORDER BY sig_count DESC
"""))
for row in age_sigs.fetchall():
    print(f"    {row[0]}: {row[1]:,}")

print(f"\n{'=' * 70}")
print("  COMPLETE")
print("=" * 70)
