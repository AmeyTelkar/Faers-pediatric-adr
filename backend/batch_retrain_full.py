"""
P0 Fix: Re-train all 80 GNN models and capture TEST AUC + VAL AUC.
Outputs a CSV file with complete results for the paper.
"""
import requests
import time
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/gnn"

ALL_QUARTERS = [
    "2025Q1", "2025Q2", "2025Q3", "2025Q4",
    "2024Q1", "2024Q2", "2024Q3", "2024Q4",
    "2023Q1", "2023Q2", "2023Q3", "2023Q4",
    "2022Q1", "2022Q2", "2022Q3", "2022Q4",
    "2021Q1", "2021Q2", "2021Q3", "2021Q4",
]

AGE_GROUPS = ["ADOLESCENT", "CHILD", "INFANT", "NEONATE"]

total = len(ALL_QUARTERS) * len(AGE_GROUPS)
done = 0
results = []

print("=" * 70)
print(f"  FULL 80-MODEL GNN RETRAINING (capturing Test AUC)")
print(f"  {total} runs ({len(ALL_QUARTERS)} quarters x {len(AGE_GROUPS)} age groups)")
print("=" * 70)

for quarter in ALL_QUARTERS:
    print(f"\n--- QUARTER: {quarter} ---")
    
    for age_group in AGE_GROUPS:
        done += 1
        print(f"  [{done}/{total}] {age_group} @ {quarter}...", end=" ", flush=True)
        start = time.time()
        
        try:
            resp = requests.post(
                f"{BASE_URL}/train/{age_group}",
                params={"epochs": 100, "quarter": quarter},
                timeout=300,
            )
            elapsed = time.time() - start
            
            if resp.status_code == 200:
                data = resp.json()
                val_auc = data.get("best_val_auc", None)
                test_auc = data.get("test_auc", None)
                test_loss = data.get("test_loss", None)
                final_loss = data.get("final_loss", None)
                n_drugs = data.get("n_drugs", None)
                n_adrs = data.get("n_adrs", None)
                n_edges = data.get("n_edges", None)
                
                results.append({
                    "quarter": quarter,
                    "age_group": age_group,
                    "val_auc": val_auc,
                    "test_auc": test_auc,
                    "test_loss": test_loss,
                    "final_loss": final_loss,
                    "n_drugs": n_drugs,
                    "n_adrs": n_adrs,
                    "n_edges": n_edges,
                })
                
                print(f"Val={val_auc} | Test={test_auc} | {elapsed:.1f}s")
            else:
                print(f"FAIL HTTP {resp.status_code} | {elapsed:.1f}s")
                results.append({
                    "quarter": quarter,
                    "age_group": age_group,
                    "val_auc": None,
                    "test_auc": None,
                    "test_loss": None,
                    "final_loss": None,
                    "n_drugs": None,
                    "n_adrs": None,
                    "n_edges": None,
                })
        except Exception as e:
            elapsed = time.time() - start
            print(f"ERROR: {str(e)[:60]} | {elapsed:.1f}s")
            results.append({
                "quarter": quarter,
                "age_group": age_group,
                "val_auc": None,
                "test_auc": None,
                "test_loss": None,
                "final_loss": None,
                "n_drugs": None,
                "n_adrs": None,
                "n_edges": None,
            })

# Save to CSV
csv_path = "gnn_full_results.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["quarter", "age_group", "val_auc", "test_auc", "test_loss", "final_loss", "n_drugs", "n_adrs", "n_edges"])
    writer.writeheader()
    writer.writerows(results)

print(f"\n{'=' * 70}")
print(f"  COMPLETE: {done} models trained")
print(f"  Results saved to: {csv_path}")
print(f"{'=' * 70}")

# Print summary table
print("\n  VALIDATION AUC SUMMARY:")
print(f"  {'Quarter':<10} {'ADOLESCENT':>12} {'CHILD':>12} {'INFANT':>12} {'NEONATE':>12}")
print(f"  {'-'*58}")
for q in ALL_QUARTERS:
    row = {r['age_group']: r['val_auc'] for r in results if r['quarter'] == q}
    print(f"  {q:<10} {row.get('ADOLESCENT','N/A'):>12} {row.get('CHILD','N/A'):>12} {row.get('INFANT','N/A'):>12} {row.get('NEONATE','N/A'):>12}")

print("\n  TEST AUC SUMMARY:")
print(f"  {'Quarter':<10} {'ADOLESCENT':>12} {'CHILD':>12} {'INFANT':>12} {'NEONATE':>12}")
print(f"  {'-'*58}")
for q in ALL_QUARTERS:
    row = {r['age_group']: r['test_auc'] for r in results if r['quarter'] == q}
    print(f"  {q:<10} {str(row.get('ADOLESCENT','N/A')):>12} {str(row.get('CHILD','N/A')):>12} {str(row.get('INFANT','N/A')):>12} {str(row.get('NEONATE','N/A')):>12}")
